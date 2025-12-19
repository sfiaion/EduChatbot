from sqlalchemy.orm import Session
from app.models.question import Assignment, StudentSubmission
from app.schemas.assignment import AssignmentCreate

def create_assignment(db: Session, assignment: AssignmentCreate, teacher_id: int):
    db_assignment = Assignment(
        title=assignment.title,
        teacher_id=teacher_id,
        class_id=assignment.class_id,
        deadline=assignment.deadline,
        assigned_student_ids=assignment.assigned_student_ids,
        assigned_question_ids=assignment.assigned_question_ids
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

def get_assignment(db: Session, assignment_id: int):
    return db.query(Assignment).filter(Assignment.id == assignment_id).first()

def get_assignment_stats_base(db: Session, assignment_id: int):
    assignment = get_assignment(db, assignment_id)
    if not assignment:
        return None
    
    # 统计已提交的学生人数（去重）
    submitted_count = db.query(StudentSubmission.student_id)\
        .filter(StudentSubmission.assignment_id == assignment_id)\
        .distinct()\
        .count()

    question_ids = assignment.assigned_question_ids or []
    
    return {
        "total_students": submitted_count, # 修改为显示已提交人数，更直观
        "total_questions": len(question_ids)
    }

def get_assignments_by_teacher(db: Session, teacher_id: int):
    return db.query(Assignment).filter(Assignment.teacher_id == teacher_id).all()

def get_assignments_by_class(db: Session, class_id: int):
    return db.query(Assignment).filter(Assignment.class_id == class_id).all()
