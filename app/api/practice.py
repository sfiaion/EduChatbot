from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db

router = APIRouter(prefix="/practice", tags=["Practice"])

class PracticeListIn(BaseModel):
    student_id: int
    ids: List[int]

class PracticeRecordIn(BaseModel):
    student_id: int
    question_id: int
    answer: str

_store: dict[int, List[int]] = {}
_records: list[PracticeRecordIn] = []

@router.get("/list")
def get_list(student_id: int, db: Session = Depends(get_db)):
    return _store.get(student_id, [])

@router.post("/list")
def save_list(data: PracticeListIn, db: Session = Depends(get_db)):
    _store[data.student_id] = list(dict.fromkeys(data.ids))
    return {"saved": len(_store[data.student_id])}

@router.post("/record")
def save_record(data: PracticeRecordIn, db: Session = Depends(get_db)):
    _records.append(data)
    return {"ok": True}
