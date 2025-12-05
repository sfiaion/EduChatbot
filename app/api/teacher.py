from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from ..crud.clazz import get_classes_by_teachers

router = APIRouter(prefix="/teacher", tags=["Teacher"])

@router.get("/classes")
def get_teacher_classes(
    db: Session = Depends(get_db),
):
    return get_classes_by_teachers(db, 1) # teacher_id先写死为1，后续再接入登录系统