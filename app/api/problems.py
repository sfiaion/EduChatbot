#app\api\problems.py
from fastapi import APIRouter, UploadFile, File, Depends, Query
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..services.load_questions import upload_questions
from fastapi import APIRouter, Depends, HTTPException
from ..crud.question import get_question_by_id, get_questions, has_wrong_submission
from ..services.recommendation import search_by_slot
from ..schemas.recommendation import RecommendationRequest, RecommendationResponse, RecommendedItem
from ..schemas.question import QuestionRead
from typing import List, Optional
from pydantic import BaseModel

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
):
    teacher_id = 1  # 先写死，后续再接入登录系统
    result = upload_questions(file, db, teacher_id)
    return result

@router.post("/{problem_id}/recommendation", response_model=RecommendationResponse)
def recommend_questions(req: RecommendationRequest, db: Session = Depends(get_db)):
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
