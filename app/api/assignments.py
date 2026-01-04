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
from app.api.notifications import create_notification
from app.models.user import Student, Class

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
    clazz = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher_id).first()
    if not clazz:
        raise HTTPException(status_code=403, detail="Class not found or not owned by current teacher")
    deadline_dt = None
    if deadline:
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            if getattr(deadline_dt, "tzinfo", None) is not None:
                deadline_dt = deadline_dt.astimezone().replace(tzinfo=None)
        except ValueError:
            pass # Or raise HTTP exception
    try:
        a = process_assignment_upload(file, db, teacher_id, class_id, deadline_dt, title)
        try:
            create_notification(db, current_user.id, "已布置作业", f"作业「{a.title or a.id}」已创建", "assignment", a.id)
            students = db.query(Student).filter(Student.class_id == class_id).all()
            for s in students:
                create_notification(db, s.user_id, "新的作业", f"收到老师布置的作业「{a.title or a.id}」", "assignment", a.id)
        except Exception:
            pass
        return a
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
    if assignment.class_id:
        clazz = db.query(Class).filter(Class.id == assignment.class_id, Class.teacher_id == current_user.teacher.id).first()
        if not clazz:
            raise HTTPException(status_code=403, detail="Class not found or not owned by current teacher")
    if assignment.deadline and getattr(assignment.deadline, "tzinfo", None) is not None:
        assignment.deadline = assignment.deadline.astimezone().replace(tzinfo=None)
    a = create_assignment(db, assignment, current_user.teacher.id)
    try:
        create_notification(db, current_user.id, "已布置作业", f"作业「{a.title or a.id}」已创建", "assignment", a.id)
        if a.class_id:
            students = db.query(Student).filter(Student.class_id == a.class_id).all()
            for s in students:
                create_notification(db, s.user_id, "新的作业", f"收到老师布置的作业「{a.title or a.id}」", "assignment", a.id)
    except Exception:
        pass
    return a

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
