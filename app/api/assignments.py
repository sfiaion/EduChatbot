from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentStats
from app.crud.assignment import create_assignment, get_assignment, get_assignment_stats_base, get_assignments_by_teacher, get_assignments_by_class
from app.services.assignment_pipeline import process_assignment_upload
from app.models.question import Question, Assignment, StudentSubmission
from app.models.user import User
from .deps import get_current_active_teacher, get_current_user

router = APIRouter(prefix="/assignments", tags=["Assignments"])

@router.get("/", response_model=List[AssignmentRead])
def list_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "teacher":         
        if not current_user.teacher:
             return []
        return get_assignments_by_teacher(db, current_user.teacher.id)
    elif current_user.role == "student":
        if not current_user.student or not current_user.student.class_id:
             return []
        assignments = get_assignments_by_class(db, current_user.student.class_id)
        # Check submissions
        student_id = current_user.student.id
        for a in assignments:
            # Check if any submission exists for this assignment
            sub = db.query(StudentSubmission).filter(
                StudentSubmission.assignment_id == a.id,
                StudentSubmission.student_id == student_id
            ).first()
            a.is_submitted = True if sub else False
        return assignments
    elif current_user.role == "admin":
         # Admin sees all for now, or implement pagination
         return db.query(Assignment).all()
    else:
        return []

@router.post("/upload", response_model=AssignmentRead)
def upload_assignment(
    file: UploadFile = File(...),
    class_id: int = Form(...),
    title: Optional[str] = Form(None),
    deadline: Optional[str] = Form(None), # Receive as string, parse manually
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_teacher)
):
    teacher_id = current_user.teacher.id
    deadline_dt = None
    if deadline:
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        except ValueError:
            pass # Or raise HTTP exception
    try:
        return process_assignment_upload(file, db, teacher_id, class_id, deadline_dt, title)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=AssignmentRead)
def create_assignment_manual(
    assignment: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_teacher)
):
    return create_assignment(db, assignment, current_user.teacher.id)

@router.get("/{id}", response_model=AssignmentRead)
def read_assignment(id: int, db: Session = Depends(get_db)):
    res = get_assignment(db, id)
    if not res:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return res

@router.get("/{id}/paper")
def get_assignment_paper(id: int, db: Session = Depends(get_db)):
    """Returns the student view of the assignment (questions without answers)"""
    assignment = get_assignment(db, id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    q_ids = assignment.assigned_question_ids
    if not q_ids:
        return []
        
    questions = db.query(Question).filter(Question.id.in_(q_ids)).all()
    
    # Return minimal data for rendering
    return [
        {
            "id": q.id,
            "question": q.question,
            # Add other non-sensitive fields if needed (e.g., difficulty, tags)
        }
        for q in questions
    ]

@router.get("/{id}/stats", response_model=AssignmentStats)
def get_stats(id: int, db: Session = Depends(get_db)):
    stats = get_assignment_stats_base(db, id)
    if not stats:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return stats
