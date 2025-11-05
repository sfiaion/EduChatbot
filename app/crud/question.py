from sqlalchemy.orm import Session
from typing import List
from app.models.question import Question, KnowledgeNode

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

