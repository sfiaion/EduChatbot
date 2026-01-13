from sqlalchemy.orm import Session
from app.models.question import StudentSubmission
from app.schemas.submission import SubmissionCreate

def create_submissions(db: Session, sub: SubmissionCreate):
    count = 0
    for ans in sub.answers:
        # Check if exists
        existing = db.query(StudentSubmission).filter(
            StudentSubmission.assignment_id == sub.assignment_id,
            StudentSubmission.student_id == sub.student_id,
            StudentSubmission.question_id == ans.question_id
        ).first()

        img = None
        if getattr(ans, "image_path", None):
            img = ans.image_path
        else:
            if isinstance(ans.student_answer, str) and ans.student_answer.startswith("[IMAGE]"):
                img = ans.student_answer.replace("[IMAGE]", "")
        
        student_text = ans.student_answer
        if img:
            student_text = ""

        if existing:
            existing.student_answer = student_text
            existing.image_path = img
            # attempt_count will be handled in process_submission or incremented here? 
            # process_submission is better place as it handles logic.
        else:
            obj = StudentSubmission(
                assignment_id=sub.assignment_id,
                student_id=sub.student_id,
                question_id=ans.question_id,
                student_answer=student_text,
                image_path=img
            )
            db.add(obj)
        count += 1
    
    db.commit()
    return count
