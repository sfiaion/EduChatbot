#app\api\problems.py
from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..services.load_questions import upload_questions
from ..crud.question import get_question_by_id, get_questions, has_wrong_submission
from ..services.recommendation import search_by_slot
from ..schemas.recommendation import RecommendationRequest, RecommendationResponse, RecommendedItem
from ..schemas.question import QuestionRead
from typing import List, Optional
from pydantic import BaseModel
from app.models.user import User
from .deps import get_current_active_teacher, get_current_active_student, get_current_user

class QuestionListResponse(BaseModel):
    total: int
    items: List[QuestionRead]

router = APIRouter(prefix="/problems", tags=["Problems"])

@router.get("/", response_model=QuestionListResponse)
def list_questions(
    skip: int = 0, 
    limit: int = 20, 
    difficulty: Optional[str] = Query(None),
    knowledge: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    items, total = get_questions(db, skip=skip, limit=limit, difficulty=difficulty, knowledge=knowledge)
    return {"total": total, "items": items}

@router.post("/upload")
def upload_question_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_teacher)
):
    teacher_id = current_user.teacher.id
    result = upload_questions(file, db, teacher_id)
    return result

@router.post("/{problem_id}/recommendation", response_model=RecommendationResponse)
def recommend_questions(
    req: RecommendationRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # If student, force student_id to self
    if current_user.role == "student":
        if not current_user.student:
             raise HTTPException(status_code=400, detail="Student profile not found")
        req.student_id = current_user.student.id
    # If teacher/admin, allow passing student_id (must be provided in req)
    elif current_user.role in ["teacher", "admin"]:
        if not req.student_id:
             raise HTTPException(status_code=400, detail="Student ID is required for teacher request")
    else:
        raise HTTPException(status_code=403, detail="Permission denied")

    question = get_question_by_id(db, req.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    final = search_by_slot(db, req.student_id, req.question_id, req.slot, req.expect_num)
    return RecommendationResponse(
        base_question_id=req.question_id,
        slot=req.slot,
        expected=req.expect_num,
        found=len(final),
        items=[RecommendedItem(id=qid, score=score) for qid, score in final]
    )

@router.get("/{id}", response_model=QuestionRead)
def read_question(id: int, db: Session = Depends(get_db)):
    q = get_question_by_id(db, id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q
