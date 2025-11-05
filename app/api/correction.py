from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db  # 假设你有这个函数
from app.schemas.correction import CorrectionRequest, CorrectionResponse, ErrorType
from ..services.correction import grade_answer_service

router = APIRouter()

@router.post("/grade", response_model=CorrectionResponse)
def grade_answer(req: CorrectionRequest, db: Session = Depends(get_db)):
    return grade_answer_service(req.question_id, req.student_answer, db)