from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..services.load_questions import upload_questions

router = APIRouter()

@router.post("/upload")
def upload_question_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    teacher_id = 1  # 先写死，后续再接入登录系统
    result = upload_questions(file, db, teacher_id)
    return result
