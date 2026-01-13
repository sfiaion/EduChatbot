from typing import List, Dict, Any
import os
import pathlib
from sqlalchemy.orm import Session
from app.schemas.submission import SubmissionCreate
from app.models.question import StudentSubmission, ErrorAnalysis
from app.services.correction import grade_answer_service
from app.ml.ocr import extract_answer_from_image
from app.api.notifications import create_notification
from app.models.user import Student as StudentModel
from app.crud.question import get_question_by_id
from app.ml.correction import generate_hint

APP_ROOT = pathlib.Path(__file__).resolve().parent.parent
STATIC_SUB_DIR = APP_ROOT / "static" / "submissions"

def _resolve_abs_image_path(img_path: str) -> str:
    p = pathlib.Path(img_path)
    if p.is_absolute():
        return str(p)
    return str(APP_ROOT / img_path)

def process_submission(sub: SubmissionCreate, db: Session) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for ans in sub.answers:
        student_text = ans.student_answer or ""
        img_path = getattr(ans, "image_path", None)
        if not img_path and isinstance(student_text, str) and student_text.startswith("[IMAGE]"):
            img_path = student_text.replace("[IMAGE]", "")
        if img_path:
            abs_path = _resolve_abs_image_path(img_path)
            if os.path.exists(abs_path):
                try:
                    ocr_text = extract_answer_from_image(abs_path)
                    student_text = ocr_text or ""
                except Exception:
                    student_text = "[OCR processing failed]"
            else:
                student_text = "[Image file not found]"
        try:
            result = grade_answer_service(ans.question_id, student_text, db)
        except Exception:
            result = None
        submission_record = db.query(StudentSubmission).filter(
            StudentSubmission.student_id == sub.student_id,
            StudentSubmission.assignment_id == sub.assignment_id,
            StudentSubmission.question_id == ans.question_id
        ).first()
        if submission_record:
            if result is not None:
                # Only increment attempt count if grading succeeded
                current_attempts = submission_record.attempt_count or 0
                submission_record.attempt_count = current_attempts + 1

                is_correct = result.is_correct
                submission_record.is_correct = is_correct
                if not is_correct:
                    # Use relationship to avoid duplicate inserts under concurrent requests
                    ea = submission_record.error_analysis
                    if not ea:
                        ea = db.query(ErrorAnalysis).filter(ErrorAnalysis.submission_id == submission_record.id).first()
                        if not ea:
                            ea = ErrorAnalysis(submission_id=submission_record.id)
                            db.add(ea)
                    ea.error_type = result.error_type
                    ea.analysis = result.analysis
                    try:
                        kid = getattr(result, "knowledge_node_id", None)
                        if not kid:
                            kid = getattr(result, "knowledge_id", None)
                        if kid and int(kid) > 0:
                            ea.knowledge_node_id = int(kid)
                    except Exception:
                        pass
                    
                    # Hint Logic
                    if submission_record.attempt_count < 3:
                        try:
                            q_obj = get_question_by_id(db, ans.question_id)
                            # Pass current attempt count to generate appropriate hint level
                            hint = generate_hint(q_obj.question, student_text, q_obj.answer, submission_record.attempt_count)
                            ea.hint = hint
                        except Exception as e:
                            print(f"Hint generation failed: {e}")
                            ea.hint = "Think about it again!"
            
            if img_path:
                submission_record.image_path = img_path
            submission_record.student_answer = student_text if student_text else "[OCR content not recognized]"

            db.commit()
            
            res_dict = {
                "question_id": ans.question_id,
                "student_answer": submission_record.student_answer,
                "image_path": submission_record.image_path,
                "is_correct": bool(submission_record.is_correct) if submission_record.is_correct is not None else False,
                "attempt_count": submission_record.attempt_count
            }
            
            if not submission_record.is_correct:
                if submission_record.attempt_count < 3 and submission_record.error_analysis:
                    res_dict["status"] = "retry"
                    res_dict["hint"] = submission_record.error_analysis.hint
                    res_dict["remaining_attempts"] = 3 - submission_record.attempt_count
                elif submission_record.error_analysis:
                    res_dict["status"] = "failed"
                    res_dict["error_type"] = submission_record.error_analysis.error_type
                    res_dict["analysis"] = submission_record.error_analysis.analysis
            else:
                res_dict["status"] = "success"
                
            results.append(res_dict)
    # Notify grading completion (best-effort)
    try:
        student = db.query(StudentModel).filter(StudentModel.id == sub.student_id).first()
        if student and student.user_id:
            create_notification(db, student.user_id, "Grading Completed", f"Assignment {sub.assignment_id} has been graded", "grading", sub.assignment_id)
    except Exception:
        pass
    return results
