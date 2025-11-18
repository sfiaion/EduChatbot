from sqlalchemy.orm import Session
from typing import List
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
    existing = db.query(Question).filter(
        Question.normalized_question == normalized_question
    ).first()
    if existing:
        return existing
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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(Question).filter(
            Question.normalized_question == normalized_question
        ).first()
        return existing
    db.refresh(db_question)
    return db_question


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

