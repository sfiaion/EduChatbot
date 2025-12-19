# api/submissions.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import tempfile
import uuid
import pathlib
from typing import List
from ..schemas.submission import SubmissionCreate
from ..ml.ocr import extract_answer_from_image, extract_blocks_from_image
from ..crud.submission import create_submissions
from ..db.session import get_db
from ..models.question import StudentSubmission, ErrorAnalysis, Question
from ..services.submission import process_submission
from pydantic import BaseModel
from ..models.user import User, Student
from .deps import get_current_active_student, get_current_user

router = APIRouter(prefix="/submissions", tags=["Submissions"])

STATIC_DIR = pathlib.Path(__file__).parent.parent / "static" / "submissions"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

class SubmissionResultResponse(BaseModel):
    question_id: int
    student_answer: str
    image_path: str | None = None
    is_correct: bool
    error_type: str = None
    analysis: str = None

@router.get("/stats/{assignment_id}")
def get_assignment_stats(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 1. Fetch all submissions
    submissions = db.query(StudentSubmission).filter(
        StudentSubmission.assignment_id == assignment_id
    ).all()

    if not submissions:
        return {
            "overall": {"average_accuracy": 0, "total_submissions": 0, "student_count": 0}, 
            "questions": [], 
            "students": [], 
            "weak_points": [],
            "error_distribution": []
        }

    # 2. Student Stats
    student_map = {}
    # Pre-fetch students to avoid N+1
    student_ids = list(set(s.student_id for s in submissions))
    students = db.query(Student).filter(Student.id.in_(student_ids)).all()
    student_name_map = {s.id: s.name for s in students}

    for sub in submissions:
        sid = sub.student_id
        if sid not in student_map:
            student_map[sid] = {
                "id": sid,
                "name": student_name_map.get(sid, f"Student {sid}"),
                "total": 0,
                "correct": 0,
                "submitted": True
            }
        
        student_map[sid]["total"] += 1
        if sub.is_correct:
            student_map[sid]["correct"] += 1

    student_list = []
    for s in student_map.values():
        s["accuracy"] = round((s["correct"] / s["total"] * 100), 1) if s["total"] > 0 else 0
        student_list.append(s)

    # 3. Question Stats
    question_map = {}
    # Pre-fetch questions
    question_ids = list(set(s.question_id for s in submissions))
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    q_text_map = {q.id: q.question for q in questions}
    q_tag_map = {q.id: q.knowledge_tag for q in questions}

    for sub in submissions:
        qid = sub.question_id
        if qid not in question_map:
            question_map[qid] = {
                "id": qid,
                "text": q_text_map.get(qid, f"Q{qid}"),
                "total": 0,
                "correct": 0,
                "wrong": 0
            }
        
        question_map[qid]["total"] += 1
        if sub.is_correct:
            question_map[qid]["correct"] += 1
        else:
            question_map[qid]["wrong"] += 1

    question_list = []
    for q in question_map.values():
        q["correct_rate"] = round((q["correct"] / q["total"] * 100), 1) if q["total"] > 0 else 0
        question_list.append(q)
    
    # Sort by correct rate (ascending) -> Hardest first
    question_list.sort(key=lambda x: x["correct_rate"])

    # 4. Weak Points (Error Analysis)
    error_counts = {}
    knowledge_counts = {}
    
    for sub in submissions:
        if not sub.is_correct:
            # Error Type
            if sub.error_analysis and sub.error_analysis.error_type:
                etype = sub.error_analysis.error_type
                error_counts[etype] = error_counts.get(etype, 0) + 1
            
            # Knowledge Tag
            tags_str = q_tag_map.get(sub.question_id)
            if tags_str:
                 # Assume tags are comma separated
                 tags = [t.strip() for t in tags_str.split(',')]
                 for t in tags:
                     if t: knowledge_counts[t] = knowledge_counts.get(t, 0) + 1

    weak_points = [
        {"tag": k, "count": v} 
        for k, v in sorted(knowledge_counts.items(), key=lambda item: item[1], reverse=True)[:5]
    ]
    
    error_dist = [
        {"name": k, "value": v}
        for k, v in error_counts.items()
    ]

    # 5. Overall
    total_correct = sum(1 for s in submissions if s.is_correct)
    total_questions_graded = len(submissions)
    total_submissions = len(student_map) # Number of students who submitted
    avg_accuracy = round((total_correct / total_questions_graded * 100), 1) if total_questions_graded > 0 else 0

    return {
        "overall": {
            "average_accuracy": avg_accuracy,
            "total_submissions": total_submissions,
            "student_count": len(student_list)
        },
        "questions": question_list,
        "students": student_list,
        "weak_points": weak_points,
        "error_distribution": error_dist
    }

@router.get("/results", response_model=List[SubmissionResultResponse])
def get_submission_results(
    assignment_id: int,
    student_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_student_id = None
    if current_user.role == "student":
        if not current_user.student:
             raise HTTPException(status_code=400, detail="Student profile not found")
        target_student_id = current_user.student.id
    elif current_user.role in ["teacher", "admin"]:
        if student_id is None:
            raise HTTPException(status_code=400, detail="Student ID required for teacher view")
        target_student_id = student_id
    else:
        raise HTTPException(status_code=403, detail="Permission denied")

    submissions = db.query(StudentSubmission).filter(
        StudentSubmission.assignment_id == assignment_id,
        StudentSubmission.student_id == target_student_id
    ).all()
    
    results = []
    for sub in submissions:
        res = SubmissionResultResponse(
            question_id=sub.question_id,
            student_answer=sub.student_answer,
            image_path=sub.image_path,
            is_correct=sub.is_correct if sub.is_correct is not None else False
        )
        if sub.is_correct is False and sub.error_analysis:
            res.error_type = sub.error_analysis.error_type
            res.analysis = sub.error_analysis.analysis
        results.append(res)
    return results

@router.post("/")
def submit_assignment(
    sub: SubmissionCreate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_student)
):
    # Force student_id to match the authenticated user
    sub.student_id = current_user.student.id
    
    count = create_submissions(db, sub)
    results = process_submission(sub, db)
    return {"status": "ok", "submitted_count": count, "results": results}

@router.post("/upload_image")
async def upload_submission_image(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Only images allowed")
    
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    filepath = STATIC_DIR / filename
    
    with open(filepath, "wb") as f:
        f.write(await file.read())
        
    # Return relative path for storage
    return {"path": f"static/submissions/{filename}", "url": f"/static/submissions/{filename}"}

@router.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Only PNG/JPG images are allowed.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        extracted_text = extract_answer_from_image(tmp_path)
        return JSONResponse({"text": extracted_text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@router.post("/ocr_split")
async def ocr_split_endpoint(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Only PNG/JPG images are allowed.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        blocks = extract_blocks_from_image(tmp_path)
        return JSONResponse({"blocks": blocks})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR split failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
