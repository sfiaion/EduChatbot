from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.question import StudentSubmission, Question

router = APIRouter(prefix="/wrongbook", tags=["Wrongbook"])

@router.get("/list")
def list_wrongbook(student_id: int = Query(...), group_by: str = Query("time"), db: Session = Depends(get_db)):
    rows = db.query(StudentSubmission, Question).join(Question, StudentSubmission.question_id == Question.id).filter(
        StudentSubmission.student_id == student_id,
        StudentSubmission.is_correct.is_(False)
    ).all()
    agg = {}
    for sub, q in rows:
        key = sub.question_id
        item = agg.get(key)
        if not item:
            agg[key] = {
                "question_id": sub.question_id,
                "question": q.question,
                "student_answer": sub.student_answer,
                "error_count": 1,
                "last_error_time": str(sub.created_at)
            }
        else:
            item["error_count"] += 1
            item["last_error_time"] = str(max(item["last_error_time"], str(sub.created_at)))
    return list(agg.values())
