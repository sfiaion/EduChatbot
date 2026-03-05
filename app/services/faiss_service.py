# app/services/faiss_service.py
import pickle
import os
import pathlib
import faiss
import numpy as np

class FaissService:
    def __init__(self, dim, index_name="faiss"):
        self.dim = dim
        self.index_name = index_name

        # 沿用您原始代码中被验证过的、最可靠的存储路径方案
        # 所有索引都将存放在 C:\Users\<YourUsername>\.educhatbot 文件夹下
        data_dir = pathlib.Path.home() / ".educhatbot"
        data_dir.mkdir(parents=True, exist_ok=True)

        # 根据 index_name 构建不同的文件名
        self.index_path = str(data_dir / f"{index_name}.index")
        self.vectors_path = str(data_dir / f"{index_name}_id2vector.pkl")

        print(f"[FaissService] Index path set to: {self.index_path}")

        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
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
        faiss.write_index(self.index, self.index_path)
        with open(self.vectors_path, "wb") as f:
            pickle.dump(self.id2vector, f)

    def delete_id(self, id):
        if id in self.id2vector:
            del self.id2vector[id]
        self.index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dim))
        ids = np.array([int(k) for k in self.id2vector.keys()], dtype=np.int64)
        vectors = np.array(list(self.id2vector.values()), dtype=np.float32)
        if len(ids) > 0:
            self.index.add_with_ids(vectors, ids)
        self.save()
