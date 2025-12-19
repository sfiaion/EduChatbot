# \app\crud\question.py
from sqlalchemy.orm import Session
from typing import List

from app.models import StudentSubmission
from app.models.question import Question, KnowledgeNode
import json
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

# def create_question(
#     db: Session,
#     question: str,
#     normalized_question: str,
#     answer: str,
#     types: list[str],
#     properties: list[str],
#     difficulty: str,
# ):
#     existing = db.query(Question).filter(
#         Question.normalized_question == normalized_question
#     ).first()
#     if existing:
#         return existing
#     knowledge_tag = {
#         "types": types,
#         "properties": properties,
#     }
#     db_question = Question(
#         question=question,
#         normalized_question=normalized_question,
#         answer=answer,
#         knowledge_tag=knowledge_tag,
#         difficulty_tag=difficulty,
#     )
#     db.add(db_question)
#     try:
#         db.commit()
#     except IntegrityError:
#         db.rollback()
#         existing = db.query(Question).filter(
#             Question.normalized_question == normalized_question
#         ).first()
#         return existing
#     db.refresh(db_question)
#     return db_question

def create_question(
    db: Session,
    question: str,
    normalized_question: str,
    answer: str,
    types: list[str],
    properties: list[str],
    difficulty: str,
):

    # ✅ 手动序列化为 JSON 字符串，确保中文不转义
    knowledge_tag = json.dumps({
        "types": types,
        "properties": properties
    }, ensure_ascii=False, separators=(',', ':'))  # 紧凑格式，无空格

    db_question = Question(
        question=question,
        normalized_question=normalized_question,
        answer=answer,
        knowledge_tag=knowledge_tag,  # ← 现在是字符串
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

def has_wrong_submission(db: Session, student_id: int, question_id: int) -> bool:
    row = db.query(StudentSubmission.id).filter(
        StudentSubmission.student_id == student_id,
        StudentSubmission.question_id == int(question_id),
        StudentSubmission.is_correct.is_(False)
    ).first()
    return row is not None

def get_difficulty(db: Session, question_id: int) -> str:
    question_id = int(question_id)
    row = db.query(Question.difficulty_tag).filter(
        Question.id == question_id
    ).first()
    # print(f"[DEBUG] qid={question_id}, query result={row}")
    if not row:
        return "easy"
    return row[0]


def get_question_by_id(db: Session, question_id: int):
    return db.query(Question).filter(Question.id == question_id).first()

def get_questions(db: Session, skip: int = 0, limit: int = 20, difficulty: str = None, knowledge: str = None):
    query = db.query(Question)
    if difficulty:
        query = query.filter(Question.difficulty_tag == difficulty)
    if knowledge:
        # Simple like search for knowledge tag (which is JSON string)
        query = query.filter(Question.knowledge_tag.like(f"%{knowledge}%"))
    
    # Return total count for pagination
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total

def get_question_by_normalized(db: Session, normalized_question: str):
    return db.query(Question).filter(Question.normalized_question == normalized_question).first()

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

