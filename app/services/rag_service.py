# app/services/rag_service.py
import os
import numpy as np
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.rag import RagPassage
from app.services.dashscope_embedding import DashScopeEmbeddingService
from app.services.faiss_service import FaissService
from typing import List, Optional

class RagService:
    def __init__(self):
        # text-embedding-v1 维度为 1536
        self.dim = 1536
        self.faiss_service = FaissService(dim=self.dim, index_name="rag_passages")
        self.emb_service = DashScopeEmbeddingService()

    def search_passages(self, query: str, k: int = 3, threshold: float = 0.7) -> List[RagPassage]:
        """
        语义搜索教材片段
        threshold: 相似度阈值 (余弦相似度)，建议 0.7 左右。
        """
        query_vector = self.emb_service.encode_query(query)
        ids, scores = self.faiss_service.search_vector(query_vector, k)
        
        # 过滤低质量结果 (Faiss IndexFlatIP 返回的是内积，对于归一化向量即余弦相似度)
        valid_ids = [int(id) for id, score in zip(ids, scores) if score >= threshold and id != -1]
        
        if not valid_ids:
            return []
            
        db: Session = SessionLocal()
        try:
            # 保持召回顺序
            passages = db.query(RagPassage).filter(RagPassage.id.in_(valid_ids)).all()
            id_map = {p.id: p for p in passages}
            return [id_map[id] for id in valid_ids if id in id_map]
        finally:
            db.close()

    def format_context(self, passages: List[RagPassage]) -> str:
        """将检索到的片段格式化为 Prompt 上下文"""
        if not passages:
            return ""
        
        context_parts = []
        for i, p in enumerate(passages, 1):
            source_info = f"《{p.source}》第 {p.page_no} 页" if p.source else "教材原文"
            category_info = f" [{p.category}]" if p.category else ""
            context_parts.append(f"【参考内容 {i} - {source_info}{category_info}】：\n{p.content}")
        
        return "\n\n".join(context_parts)
