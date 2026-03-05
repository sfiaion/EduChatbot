# app/services/dashscope_embedding.py
import os
import dashscope
from dashscope import TextEmbedding
from typing import List
import numpy as np

class DashScopeEmbeddingService:
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not found in environment variables")
        dashscope.api_key = self.api_key

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        使用 DashScope text-embedding-v1 接口进行向量化
        支持长文本 (2048 tokens)，输出 1536 维向量
        """
        try:
            resp = TextEmbedding.call(
                model=TextEmbedding.Models.text_embedding_v1,
                input=texts
            )
            if resp.status_code == 200:
                embeddings = [item['embedding'] for item in resp.output['embeddings']]
                return np.array(embeddings, dtype=np.float32)
            else:
                raise Exception(f"DashScope Embedding failed: {resp.code} - {resp.message}")
        except Exception as e:
            print(f"Error calling DashScope Embedding: {e}")
            raise e

    def encode_query(self, query: str) -> np.ndarray:
        """向量化单个查询字符串"""
        return self.encode([query])[0]
