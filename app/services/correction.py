from app.crud.question import get_question_by_id, get_candidate_knowledge_nodes
from app.ml.correction import grading_logic, identify_knowledge_from_candidates
from sqlalchemy.orm import Session
from app.schemas.correction import ErrorType
import json


def grade_answer_service(question_id: int, student_answer: str, db: Session):
    question = get_question_by_id(db, question_id)
    tag = question.knowledge_tag or {}
    if isinstance(tag, str):
        try:
            tag = json.loads(tag)
        except Exception:
            tag = {}
    function_types = tag.get("types") or tag.get("function_types") or []
    function_properties = tag.get("properties") or tag.get("function_properties") or []

    result = grading_logic(
        question.question,
        student_answer,
        question.answer
    )
    knowledge_id = None
    if not result.is_correct:
        candidates = get_candidate_knowledge_nodes(db, function_types, function_properties)
        knowledge_id = identify_knowledge_from_candidates(
            question=question.question,
            student_answer=student_answer,
            correct_answer=question.answer,
            candidates=candidates
        )
        if (not knowledge_id or int(knowledge_id) <= 0) and candidates:
            knowledge_id = int(candidates[0].id)
    try:
        if knowledge_id and int(knowledge_id) > 0:
            setattr(result, "knowledge_node_id", int(knowledge_id))
    except Exception:
        pass
    return result
