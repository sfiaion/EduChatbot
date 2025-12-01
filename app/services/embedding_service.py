from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('shibing624/text2vec-base-chinese')

    def build_text(self, questions):
        texts = []
        for q in questions:
            if hasattr(q, 'knowledge_tag'):
                # Question ORM
                types = q.knowledge_tag["types"]
                properties = q.knowledge_tag["properties"]
            else:
                # ParsedQuestion
                types = q.types
                properties = q.properties
            parts = []
            parts.append(f"[函数类型：{types}]")
            parts.append(f"[函数性质：{properties}]")
            parts.append(q.question)
            texts.append(" ".join(parts))
        return texts

    def encode(self, questions):
        texts = self.build_text(questions)
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings