from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentStats
from app.crud.assignment import create_assignment, get_assignment, get_assignment_stats_base
from app.services.assignment_pipeline import process_assignment_upload
from app.models.question import Question

router = APIRouter(prefix="/assignments", tags=["Assignments"])

@router.post("/upload", response_model=AssignmentRead)
def upload_assignment(
    file: UploadFile = File(...),
    teacher_id: int = Form(...),
    class_id: int = Form(...),
    title: Optional[str] = Form(None),
    deadline: Optional[str] = Form(None), # Receive as string, parse manually
    db: Session = Depends(get_db)
):
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
    db: Session = Depends(get_db)
):
    # Ensure teacher_id matches logic (e.g. current user)
    # For now, trust the input or overwrite if we had auth
    return create_assignment(db, assignment, assignment.teacher_id)

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
