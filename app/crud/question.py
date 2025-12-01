from sqlalchemy.orm import Session
from typing import List

from app.models import StudentSubmission
from app.models.question import Question, KnowledgeNode
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

def create_question(
    db: Session,
    question: str,
    normalized_question: str,
    answer: str,
    types: list[str],
    properties: list[str],
    difficulty: str,
):

    knowledge_tag = {
        "types": types,
        "properties": properties,
    }
    db_question = Question(
        question=question,
        normalized_question=normalized_question,
        answer=answer,
        knowledge_tag=knowledge_tag,
        difficulty_tag=difficulty,
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def is_norm_duplicate(db: Session, normalized_question: str):
    existing = db.query(Question).filter(
        Question.normalized_question == normalized_question
    ).first()
    if existing:
        return True
    return False

def get_done_questions(db: Session, student_id: int) -> set[int]:
    rows = db.query(StudentSubmission.question_id).filter(
        StudentSubmission.student_id == student_id
    ).all()
    return {r[0] for r in rows}

def get_difficulty(db: Session, question_id: int) -> str:
    question_id = int(question_id)
    row = db.query(Question.difficulty_tag).filter(
        Question.id == question_id
    ).first()
    # print(f"[DEBUG] qid={question_id}, query result={row}")
    return row[0]

def get_question_by_id(db: Session, question_id: int):
    return db.query(Question).filter(Question.id == question_id).first()

def get_candidate_knowledge_nodes(
    db: Session,
    function_types: List[str],
    function_properties: List[str]
) -> List[KnowledgeNode]:
    all_nodes = []
    if function_types and function_properties:
        for ft in function_types:
            for fp in function_properties:
                nodes = db.query(KnowledgeNode).filter(
                    KnowledgeNode.function_type == ft,
                    KnowledgeNode.function_property == fp
                ).all()
                all_nodes.extend(nodes)
    if function_types:
        for ft in function_types:
            nodes = db.query(KnowledgeNode).filter(
                KnowledgeNode.function_type == ft,
                KnowledgeNode.function_property.is_(None)
            ).all()
            all_nodes.extend(nodes)
    if function_properties:
        for fp in function_properties:
            nodes = db.query(KnowledgeNode).filter(
                KnowledgeNode.function_type.is_(None),
                KnowledgeNode.function_property == fp
            ).all()
            all_nodes.extend(nodes)
    generic_nodes = db.query(KnowledgeNode).filter(
            KnowledgeNode.function_type.is_(None),
            KnowledgeNode.function_property.is_(None)
        ).all()
    all_nodes.extend(generic_nodes)
    return all_nodes

