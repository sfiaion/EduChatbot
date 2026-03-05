# app/db/import_rag_vector.py
import sys
import pathlib
import numpy as np
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Add project root to sys.path
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.models.rag import RagPassage
from app.services.dashscope_embedding import DashScopeEmbeddingService
from app.services.faiss_service import FaissService

def import_rag_passages_to_faiss():
    # 加载环境变量
    dotenv_path = PROJECT_ROOT / '.env'
    load_dotenv(dotenv_path=dotenv_path, encoding='utf-8')

    db: Session = SessionLocal()
    try:
        passages = db.query(RagPassage).order_by(RagPassage.id.asc()).all()
        print(f"从数据库中读取 {len(passages)} 个教材片段")

        if not passages:
            print("数据库中没有教材片段，请先运行 ingest_textbook.py")
            return

        emb_service = DashScopeEmbeddingService()
        
        # 批量处理 (DashScope 建议单次输入文本数量限制，通常为 25 或根据 Token 限制)
        batch_size = 20
        all_embeddings = []
        all_ids = []
        
        for i in range(0, len(passages), batch_size):
            batch = passages[i:i + batch_size]
            texts = [p.content for p in batch]
            ids = [p.id for p in batch]
            
            print(f"  正在向量化第 {i} 到 {i + len(batch)} 个片段...")
            try:
                embeddings = emb_service.encode(texts)
                all_embeddings.append(embeddings)
                all_ids.extend(ids)
            except Exception as e:
                print(f"  ⚠️ 向量化批次失败: {e}")
                continue
        
        if not all_embeddings:
            print("没有成功生成向量，退出")
            return

        embeddings_np = np.vstack(all_embeddings)
        ids_np = np.array(all_ids, dtype=np.int64)
        
        dim = embeddings_np.shape[1]
        print(f"向量维度: {dim}")
        
        # 使用独立的索引名称 rag_passages
        faiss_service = FaissService(dim=dim, index_name="rag_passages")
        faiss_service.add(embeddings_np, ids_np)
        
        print(f"\n✅ RAG 向量库已更新并保存到: {faiss_service.index_path}")
        print(f"当前索引总向量数: {faiss_service.index.ntotal}")

    finally:
        db.close()

if __name__ == "__main__":
    import_rag_passages_to_faiss()
