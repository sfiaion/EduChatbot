# app/services/faiss.py
import pickle
import os
import pathlib
import faiss
import numpy as np

class FaissService:
    def __init__(self, dim):
        self.dim = dim
        app_root = pathlib.Path(__file__).resolve().parent.parent
        env_dir = os.environ.get("EDUCHATBOT_FAISS_DIR")
        if env_dir:
            data_dir = pathlib.Path(env_dir)
        else:
            data_dir = pathlib.Path.home() / ".educhatbot"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = str(data_dir / "faiss.index")
        self.vectors_path = str(data_dir / "id2vector.pkl")
        if os.path.exists(self.index_path):
            # print("加载已有 FAISS index")
            self.index = faiss.read_index(self.index_path)
        else:
            # print("创建新 FAISS index")
            self.index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
        if os.path.exists(self.vectors_path):
            with open(self.vectors_path, "rb") as f:
                self.id2vector = pickle.load(f)
        else:
            self.id2vector = {}
        self.ntotal = self.index.ntotal

    def add(self, vectors, ids):
        self.index.add_with_ids(
            vectors.astype(np.float32),
            ids.astype(np.int64),
        )
        for id, vector in zip(ids, vectors):
            self.id2vector[int(id)] = vector.astype(np.float32)
        self.save()

    def get_vector_by_id(self, id):
        try:
            key = int(id)
        except Exception:
            key = id
        return self.id2vector.get(key)

    def search_vector(self, vector, k):
        vector = vector.reshape(1, -1).astype(np.float32)
        scores, ids = self.index.search(vector, k)
        return ids[0], scores[0]

    def save(self):
        # 保存索引
        faiss.write_index(self.index, self.index_path)
        # 保存 id -> vector 映射
        with open(self.vectors_path, "wb") as f:
            pickle.dump(self.id2vector, f)

    # faiss_service.delete_id(question_id) 删除指定题目
    def delete_id(self, id):
        if id in self.id2vector:
            del self.id2vector[id]
        # 重建索引
        self.index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dim))
        ids = np.array([int(k) for k in self.id2vector.keys()], dtype=np.int64)
        vectors = np.array(list(self.id2vector.values()), dtype=np.float32)
        if len(ids) > 0:
            self.index.add_with_ids(vectors, ids)
        self.save()
