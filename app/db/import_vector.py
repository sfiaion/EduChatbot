import sys
import pathlib
from sqlalchemy.orm import Session
from app.models import Question
from app.db.session import SessionLocal
from ..services.embedding_service import EmbeddingService  # 你的 embedding 类
from ..services.faiss_service import FaissService          # 你的 faiss 类
import numpy as np

def import_all_questions_to_faiss():

    db: Session = SessionLocal()

    questions = db.query(Question).order_by(Question.id.asc()).all()
    print(f"从数据库中读取 {len(questions)} 道题目")

    if len(questions) == 0:
        print("数据库中没有题目，退出")

    emb_service = EmbeddingService()

    embeddings = emb_service.encode(questions)  # shape = (num_questions, dim)
    embeddings = embeddings.astype(np.float32)  # Faiss 要求 float32

    dim = embeddings.shape[1]
    faiss_service = FaissService(dim)

    new_ids = np.array([q.id for q in questions], dtype=np.int64)

    faiss_service.add(embeddings, new_ids)
    print(f"已一次性加入 {len(embeddings)} 个向量到 Faiss")

    print(f"✅ Faiss 向量库已保存到 {faiss_service.index_path}")
    print(f"Faiss 索引总向量数: {faiss_service.index.ntotal}")

    db.close()

if __name__ == "__main__":
    import_all_questions_to_faiss()
