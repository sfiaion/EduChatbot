from .faiss_service import FaissService
from ..crud.question import get_done_questions, get_difficulty
from sqlalchemy.orm import Session

def search_by_slot(db: Session, student_id: int, question_id: int, slot, expect_num):
    slot_ranges = {
        "high": (0.75, 1.0),
        "mid": (0.6, 0.9),
        "low": (0.4, 0.75)
    }
    allowed_difficulties_range = {
        "easy": ["easy", "medium"],
        "medium": ["medium", "hard"],
        "hard": ["hard"]
    }
    left, right = slot_ranges[slot]
    done_set = get_done_questions(db, student_id)
    current_difficulty = (get_difficulty(db, question_id) or "").strip().lower()
    if current_difficulty in {"易", "简单"}:
        current_difficulty = "easy"
    elif current_difficulty in {"中", "普通"}:
        current_difficulty = "medium"
    elif current_difficulty in {"难", "困难"}:
        current_difficulty = "hard"
    if current_difficulty not in allowed_difficulties_range:
        current_difficulty = "medium"
    allowed_difficulties = allowed_difficulties_range[current_difficulty]

    faiss_service = FaissService(dim=768)
    index_size = faiss_service.index.ntotal
    vector = faiss_service.get_vector_by_id(question_id)
    if vector is None:
        return []

    # print(f"[DEBUG] question_id={question_id}, vector shape={vector.shape}, index_size={index_size}")

    k = max(50, min(200, index_size))
    difficulty_cache = {}
    while True:
        ids, scores = faiss_service.search_vector(vector, k=k)
        candidates = []
        candidate_scores = {}
        for qid, score in zip(ids, scores):
            # 排除自己
            if qid == question_id:
                continue
            # 相似度过滤
            if not (left <= score <= right):
                continue
            # 学生是否做过
            if qid in done_set:
                continue
            # 难度是否符合
            if qid in difficulty_cache:
                q_difficulty = difficulty_cache.get(qid)
            else:
                q_difficulty = get_difficulty(db, qid)
                difficulty_cache[qid] = q_difficulty
            qd = (q_difficulty or "").strip().lower()
            if qd in {"易", "简单"}:
                qd = "easy"
            elif qd in {"中", "普通"}:
                qd = "medium"
            elif qd in {"难", "困难"}:
                qd = "hard"
            if qd not in allowed_difficulties:
                continue
            prev = candidate_scores.get(int(qid))
            if prev is None or score > prev:
                candidate_scores[int(qid)] = float(score)
        for qid, sc in candidate_scores.items():
            candidates.append((qid, sc))

        # print(f"[DEBUG] 当前 candidates={candidates}")

        if len(candidates) >= expect_num:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[:expect_num]
        if k >= index_size:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates
        k = min(k * 2, index_size)

