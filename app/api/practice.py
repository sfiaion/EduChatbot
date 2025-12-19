from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.question import StudentSubmission, Question
from .deps import get_current_active_student
from datetime import datetime

router = APIRouter(prefix="/practice", tags=["Practice"])

class PracticeListIn(BaseModel):
    student_id: int
    ids: List[int]

class PracticeRecordIn(BaseModel):
    student_id: int
    question_id: int
    answer: str

class PracticeSubmit(BaseModel):
    question_id: int
    answer: str

_store: dict[int, List[int]] = {}
_records: list[PracticeRecordIn] = []

@router.get("/list")
def get_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_student)):
    return _store.get(current_user.student.id, [])

@router.post("/list")
def save_list(data: PracticeListIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_student)):
    data.student_id = current_user.student.id
    _store[data.student_id] = list(dict.fromkeys(data.ids))
    return {"saved": len(_store[data.student_id])}

@router.post("/record")
def save_record(data: PracticeRecordIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_student)):
    data.student_id = current_user.student.id
    _records.append(data)
    return {"ok": True}

@router.post("/submit")
def submit_practice(
    data: PracticeSubmit, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_student)
):
    # 1. Get Question
    question = db.query(Question).filter(Question.id == data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # 2. Check Answer (Simple string match for now)
    # Using normalized comparison could be better
    is_correct = data.answer.strip() == question.answer.strip()
    
    # 3. Create Submission Record
    submission = StudentSubmission(
        question_id=data.question_id,
        student_id=current_user.student.id,
        assignment_id=None, # Practice
        student_answer=data.answer,
        is_correct=is_correct,
        created_at=datetime.now()
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    return {
        "is_correct": is_correct,
        "correct_answer": question.answer
    }
