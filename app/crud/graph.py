from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple, Optional
from sqlalchemy import func

from ..models.question import StudentSubmission, ErrorAnalysis, KnowledgeNode
from ..models.user import Student

def preload_knowledge_stats(
    db: Session,
    class_id: int,
    start_date: datetime,
    end_date: datetime,
) -> Tuple[Dict[str, int], Dict[str, Dict[str, int]]]:
    results = (
        db.query(
            KnowledgeNode.name,
            func.date(StudentSubmission.created_at).label("submit_date"),
            func.count().label("error_count") # count是当天该知识点的出错频次
        )
        .join(ErrorAnalysis, ErrorAnalysis.knowledge_node_id == KnowledgeNode.id)
        .join(StudentSubmission, ErrorAnalysis.submission_id == StudentSubmission.id)
        .join(Student, StudentSubmission.student_id == Student.id)
        .filter(
            Student.class_id == class_id,
            KnowledgeNode.name.isnot(None),
            StudentSubmission.created_at >= start_date,
            StudentSubmission.created_at <= end_date,
        )
        .group_by(KnowledgeNode.name, func.date(StudentSubmission.created_at))
        .all()
    )

    daily_errors: Dict[str, Dict[str, int]] = {}
    total_errors: Dict[str, int] = {}
    all_nodes = db.query(KnowledgeNode.name).all()
    all_names = [n[0] for n in all_nodes]
    start_d = start_date.date()
    end_d = end_date.date()
    all_dates = [str(start_d + timedelta(days=i)) for i in range((end_d - start_d).days + 1)]
    # 初始化全部知识点
    for name in all_names:
        total_errors.setdefault(name, 0)
        daily_errors.setdefault(name, {d: 0 for d in all_dates})

    for row in results:
        name = row.name
        date_str = str(row.submit_date)
        cnt = row.error_count
        daily_errors[name][date_str] = cnt
        total_errors[name] += cnt

    return total_errors, daily_errors

def get_knowledge_node_by_name(db: Session, name: str) -> KnowledgeNode:
    return db.query(KnowledgeNode).filter(KnowledgeNode.name == name).first()

def search_knowledge_nodes_by_name(db: Session, q: str):
    query = db.query(KnowledgeNode.name).filter(
        func.lower(KnowledgeNode.name).like(func.lower(f"%{q}%"))
    ).limit(20)

    results = query.all()
    return [{"name": name} for (name,) in results]

def list_all_knowledge_nodes(db: Session, limit: int = 500):
    query = db.query(KnowledgeNode.name).order_by(KnowledgeNode.name.asc()).limit(limit)
    results = query.all()
    return [{"name": name} for (name,) in results]
