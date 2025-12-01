import re
import os
import numpy as np
from ..ml.classify_questions_from_teachers import auto_labels
from ..utils.convert_file import parse_document
from ..utils.manage_dir import new_task_tmp_dir, clear_dir
from ..crud.question import create_question, is_norm_duplicate
from .embedding_service import EmbeddingService
from .faiss_service import FaissService
from sqlalchemy.orm import Session
from fastapi import UploadFile
from dataclasses import dataclass
from typing import List

@dataclass
class ParsedQuestion:
    question: str
    normalized_question: str
    answer: str
    types: List[str]
    properties: List[str]
    difficulty: str

def upload_questions(file: UploadFile, db: Session, teacher_id: int):
    tmp_dir = new_task_tmp_dir()
    input_path = os.path.join(tmp_dir, file.filename)
    try:
        with open(input_path, "wb") as f:
            f.write(file.file.read())
        file_to_questions(input_path, db, tmp_dir)
        return {"status": "success"}
    except Exception as e:
        print("Error during upload:", e)
        return {"error": str(e)}
    finally:
        clear_dir(tmp_dir)



def file_to_questions(path, db: Session, tmp_dir: str):
    final_text = parse_document(path, tmp_dir)
    final_list = [line.strip() for line in final_text.split("\n") if line.strip()]

    raw_questions: List[ParsedQuestion] = []

    for i in range(0, len(final_list), 2):
        question_str = re.sub(r'\s*\|\|\s*', '\n', final_list[i])
        answer_str = re.sub(r'\s*\|\|\s*', '\n', final_list[i + 1]) if i + 1 < len(final_list) else ""

        raw_questions.append(ParsedQuestion(
            question=question_str,
            normalized_question=normalize_text(question_str),
            answer=answer_str,
            types=[],
            properties=[],
            difficulty=""
        ))

    # 清空表
    # db.query(Question).delete()
    # db.commit()
    for raw_question in raw_questions:
        types, properties, difficulty = auto_labels(raw_question.question, raw_question.answer)
        # print(types)
        # print(properties)
        # print(difficulty)
        raw_question.types = types
        raw_question.properties = properties
        raw_question.difficulty = difficulty

    norm_dedup_questions: List[ParsedQuestion] = []
    for raw_question in raw_questions:
        if not is_norm_duplicate(db, raw_question.normalized_question):
            norm_dedup_questions.append(raw_question)
    # print(f"norm_dedup_questions:{norm_dedup_questions}")

    emb_service = EmbeddingService()
    faiss_service = FaissService(dim=768)
    embed_dedup_questions = []
    new_embeddings = []
    new_ids = []
    if not norm_dedup_questions:
        pass
    elif faiss_service.ntotal == 0:
        embed_dedup_questions = norm_dedup_questions
        new_embeddings = emb_service.encode(norm_dedup_questions).astype(np.float32)
    else:
        embeddings = emb_service.encode(norm_dedup_questions).astype(np.float32)
        scores, _ = faiss_service.index.search(embeddings, k=1)
        for idx, q in enumerate(norm_dedup_questions):
            if scores[idx, 0] < 0.99:
                embed_dedup_questions.append(q)
                new_embeddings.append(embeddings[idx])
        if new_embeddings:
            new_embeddings = np.stack(new_embeddings)
        else:
            new_embeddings = np.empty((0, 768), dtype=np.float32)
    # print(f"embed_dedup_questions:{embed_dedup_questions}")

    for embed_dedup_question in embed_dedup_questions:
        db_question = create_question(
            db,
            embed_dedup_question.question,
            embed_dedup_question.normalized_question,
            embed_dedup_question.answer,
            embed_dedup_question.types,
            embed_dedup_question.properties,
            embed_dedup_question.difficulty
        )

        # print(db_question.question)
        # print(db_question.answer)
        # print(db_question.knowledge_tag["types"])
        # print(db_question.knowledge_tag["properties"])
        # print(db_question.difficulty_tag)
        new_ids.append(db_question.id)
        if len(new_embeddings) > 0:
            faiss_service.add(new_embeddings, new_ids)



def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\s+', '', text)               # 去掉所有空白
    text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)  # 去掉符号，仅保留中英文与数字
    text = re.sub(r'_+', '', text)
    return text