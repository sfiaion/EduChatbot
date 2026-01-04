from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.user import User, Student, Teacher, Class
from app.models.clazz import ClassRequest
from app.api.deps import get_current_user, get_current_active_teacher
from app.api.notifications import create_notification
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/classes", tags=["Classes"])

class ClassMember(BaseModel):
    id: int
    name: str
    role: str # 'teacher' or 'student'
    student_number: Optional[str] = None
    
class ClassInfo(BaseModel):
    id: int
    name: str

class ClassRequestOut(BaseModel):
    id: int
    student_name: str
    class_name: str
    type: str
    status: str
    created_at: datetime

@router.get("/members", response_model=List[ClassMember])
def get_class_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    members = []
    
    if current_user.role == "teacher":
        if not current_user.teacher or not current_user.teacher.classes:
             return []
        # For simplicity, assuming teacher manages one main class or we list all students from all classes
        # User requirement: "see all people in a class"
        # Let's list for all classes owned by teacher
        for c in current_user.teacher.classes:
             members.append(ClassMember(id=current_user.teacher.id, name=current_user.teacher.name, role="teacher"))
             for s in c.students:
                 members.append(ClassMember(id=s.id, name=s.name, role="student", student_number=s.student_number))
    
    elif current_user.role == "student":
        if not current_user.student or not current_user.student.class_id:
             return []
        clazz = db.query(Class).filter(Class.id == current_user.student.class_id).first()
        if clazz:
            if clazz.teacher:
                members.append(ClassMember(id=clazz.teacher.id, name=clazz.teacher.name, role="teacher"))
            for s in clazz.students:
                members.append(ClassMember(id=s.id, name=s.name, role="student", student_number=s.student_number))
    
    # Remove duplicates
    seen = set()
    unique_members = []
    for m in members:
        key = (m.role, m.id)
        if key not in seen:
            seen.add(key)
            unique_members.append(m)
            
    return unique_members
    
@router.get("/my", response_model=List[ClassInfo])
def list_my_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_teacher)
):
    if not current_user.teacher:
        return []
    return [ClassInfo(id=c.id, name=c.name) for c in current_user.teacher.classes or []]

@router.post("/create")
def create_class(
    class_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_teacher)
):
    if not class_name or not class_name.strip():
        raise HTTPException(status_code=400, detail="Class name required")
    clazz = Class(name=class_name.strip(), teacher_id=current_user.teacher.id)
    db.add(clazz)
    db.commit()
    db.refresh(clazz)
    return {"class_id": clazz.id, "class_name": clazz.name}

@router.post("/join")
def join_class(
    class_name: str, # Student search by class name
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can join classes")
    
    clazz = db.query(Class).filter(Class.name == class_name).first()
    if not clazz:
        raise HTTPException(status_code=404, detail="Class not found")
        
    # Check if already in class
    if current_user.student.class_id == clazz.id:
        raise HTTPException(status_code=400, detail="Already in this class")
        
    # Check if request exists
    existing = db.query(ClassRequest).filter(
        ClassRequest.student_id == current_user.student.id,
        ClassRequest.class_id == clazz.id,
        ClassRequest.status == "pending"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Request already sent")
        
    req = ClassRequest(
        class_id=clazz.id,
        student_id=current_user.student.id,
        type="apply"
    )
    db.add(req)
    
    # Notify Teacher
    create_notification(db, clazz.teacher.user_id, "申请入班", f"学生 {current_user.student.name} 申请加入班级 {clazz.name}", "class_request", req.id)
    
    return {"status": "ok", "detail": "Request sent"}

@router.post("/invite")
def invite_student(
    student_username: str,
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "teacher":
         raise HTTPException(status_code=403, detail="Only teachers can invite")
    
    target_user = db.query(User).filter(User.username == student_username, User.role == "student").first()
    if not target_user or not target_user.student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    clazz = db.query(Class).filter(Class.id == class_id, Class.teacher_id == current_user.teacher.id).first()
    if not clazz:
        raise HTTPException(status_code=404, detail="Class not found or not owned")
    
    if target_user.student.class_id == clazz.id:
         raise HTTPException(status_code=400, detail="Student already in class")

    req = ClassRequest(
        class_id=clazz.id,
        student_id=target_user.student.id,
        type="invite"
    )
    db.add(req)
    
    # Notify Student
    create_notification(db, target_user.id, "班级邀请", f"老师 {current_user.teacher.name} 邀请您加入班级 {clazz.name}", "class_invite", req.id)
    
    return {"status": "ok"}

@router.get("/requests", response_model=List[ClassRequestOut])
def list_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "teacher":
        # Show applications to my classes
        class_ids = [c.id for c in current_user.teacher.classes]
        reqs = db.query(ClassRequest).filter(
            ClassRequest.class_id.in_(class_ids),
            ClassRequest.type == "apply",
            ClassRequest.status == "pending"
        ).all()
    elif current_user.role == "student":
        # Show invitations to me
        reqs = db.query(ClassRequest).filter(
            ClassRequest.student_id == current_user.student.id,
            ClassRequest.type == "invite",
            ClassRequest.status == "pending"
        ).all()
    else:
        return []
        
    return [
        ClassRequestOut(
            id=r.id,
            student_name=r.student.name,
            class_name=r.clazz.name,
            type=r.type,
            status=r.status,
            created_at=r.created_at
        ) for r in reqs
    ]

@router.post("/requests/{id}/{action}")
def handle_request(
    id: int,
    action: str, # 'accept' or 'reject'
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = db.query(ClassRequest).filter(ClassRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    # Permission check
    if current_user.role == "teacher":
        # Teacher can handle 'apply' requests for their classes
        if req.type != "apply" or req.clazz.teacher_id != current_user.teacher.id:
             raise HTTPException(status_code=403, detail="Permission denied")
    elif current_user.role == "student":
        # Student can handle 'invite' requests for themselves
        if req.type != "invite" or req.student_id != current_user.student.id:
             raise HTTPException(status_code=403, detail="Permission denied")
             
    if action == "accept":
        req.status = "accepted"
        # Update student class
        student = db.query(Student).filter(Student.id == req.student_id).first()
        student.class_id = req.class_id
        
        # Notify counterpart
        if current_user.role == "teacher":
            create_notification(db, student.user_id, "入班申请通过", f"您已加入班级 {req.clazz.name}", "system")
        else:
            create_notification(db, req.clazz.teacher.user_id, "邀请已接受", f"学生 {student.name} 已加入班级 {req.clazz.name}", "system")
            
    elif action == "reject":
        req.status = "rejected"
    
    db.commit()
    return {"status": "ok"}
