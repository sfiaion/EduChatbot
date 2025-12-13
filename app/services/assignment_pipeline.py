import os
import re
import numpy as np
from fastapi import UploadFile
from sqlalchemy.orm import Session
from typing import List, Tuple
from datetime import datetime

from app.crud.question import create_question, get_question_by_normalized
from app.ml.classify_questions_from_teachers import auto_labels
from app.services.embedding_service import EmbeddingService
from app.services.faiss_service import FaissService
from app.utils.convert_file import parse_document
from app.utils.manage_dir import new_task_tmp_dir, clear_dir
from app.schemas.assignment import AssignmentCreate
from app.crud.assignment import create_assignment
import difflib
from app.models.question import Question

class ParsedQuestion:
    def __init__(self, question, normalized_question, answer):
        self.question = question
        self.normalized_question = normalized_question
        self.answer = answer
        self.types = []
        self.properties = []
        self.difficulty = ""

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\s+', '', text)
    text = re.sub(r'[^\w\u4e00-\u9fff+\-\*/=<>\(\)\[\]]', '', text)
    text = re.sub(r'_+', '', text)
    return text

def process_assignment_upload(
    file: UploadFile, 
    db: Session, 
    teacher_id: int,
    class_id: int,
    deadline: datetime = None,
    title: str = None
):
    tmp_dir = new_task_tmp_dir()
    input_path = os.path.join(tmp_dir, file.filename)
    
    if not title:
        title = f"Assignment - {file.filename}"
    
    try:
        # 1. Save and parse file
        with open(input_path, "wb") as f:
            f.write(file.file.read())
            
        final_text = parse_document(input_path, tmp_dir)
        final_list = [line.strip() for line in final_text.split("\n") if line.strip()]
        
        parsed_questions = []
        for i in range(0, len(final_list), 2):
            question_str = re.sub(r'\s*\|\|\s*', '\n', final_list[i])
            answer_str = re.sub(r'\s*\|\|\s*', '\n', final_list[i + 1]) if i + 1 < len(final_list) else ""
            
            pq = ParsedQuestion(
                question=question_str,
                normalized_question=normalize_text(question_str),
                answer=answer_str
            )
            parsed_questions.append(pq)

        assignment_q_ids = []
        candidates_for_embedding = []
        
        # 2. Check exact text duplicates (Normalized)
        for pq in parsed_questions:
            existing = get_question_by_normalized(db, pq.normalized_question)
            if existing:
                assignment_q_ids.append(existing.id)
            else:
                # Prepare for semantic check / creation
                types, properties, difficulty = auto_labels(pq.question, pq.answer)
                pq.types = types
                pq.properties = properties
                pq.difficulty = difficulty
                candidates_for_embedding.append(pq)
        
        # 3. Check semantic duplicates (Embedding/FAISS) and Create New
        if candidates_for_embedding:
            emb_service = EmbeddingService()
            faiss_service = FaissService(dim=768)
            
            # Compute embeddings for all candidates
            embeddings = emb_service.encode(candidates_for_embedding).astype(np.float32)
            
            # If FAISS has data, search
            if faiss_service.ntotal > 0:
                scores, ids = faiss_service.index.search(embeddings, k=1)
            else:
                # Mock scores if empty
                scores = np.zeros((len(embeddings), 1))
                ids = np.zeros((len(embeddings), 1))

            new_embeddings = []
            new_ids_for_faiss = []
            
            for idx, pq in enumerate(candidates_for_embedding):
                # Check similarity (if FAISS was not empty)
                is_duplicate = False
                if faiss_service.ntotal > 0:
                    existing_id = int(ids[idx, 0])
                    existing_q = db.query(Question).filter(Question.id == existing_id).first()
                    existing_norm = existing_q.normalized_question if existing_q else ""
                    sim = difflib.SequenceMatcher(None, pq.normalized_question, existing_norm).ratio() if existing_norm else 0.0
                    if scores[idx, 0] >= 0.99 and sim >= 0.90:
                        is_duplicate = True
                        assignment_q_ids.append(existing_id)

                if not is_duplicate:
                    # Create new question
                    db_q = create_question(
                        db,
                        pq.question,
                        pq.normalized_question,
                        pq.answer,
                        pq.types,
                        pq.properties,
                        pq.difficulty
                    )
                    assignment_q_ids.append(db_q.id)
                    new_embeddings.append(embeddings[idx])
                    new_ids_for_faiss.append(db_q.id)
            
            # Add new vectors to FAISS
            if new_embeddings:
                faiss_service.add(np.stack(new_embeddings), np.array(new_ids_for_faiss))

        # 4. Create Assignment
        assignment_create = AssignmentCreate(
            title=title,
            teacher_id=teacher_id,
            class_id=class_id,
            deadline=deadline,
            assigned_student_ids=[], # Default empty, teacher can assign later
            assigned_question_ids=assignment_q_ids
        )
        
        db_assignment = create_assignment(db, assignment_create, teacher_id)
        return db_assignment

    finally:
        clear_dir(tmp_dir)
