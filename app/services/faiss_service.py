import pickle

import faiss
import numpy as np
import os

class FaissService:
    def __init__(self, dim):
        self.dim = dim
        self.index_path = "faiss.index"
        self.vectors_path = "id2vector.pkl"
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
            self.id2vector[id] = vector.astype(np.float32)
        self.save()

    def get_vector_by_id(self, id):
        return self.id2vector[id]

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
        ids = np.array(list(self.id2vector.keys()), dtype=np.int64)
        vectors = np.array(list(self.id2vector.values()), dtype=np.float32)
        if len(ids) > 0:
            self.index.add_with_ids(vectors, ids)
        self.save()
