from .faiss_service import FaissService
from ..crud.question import get_done_questions, get_difficulty
from sqlalchemy.orm import Session

def search_by_slot(db: Session, student_id: int, question_id: int, slot, expect_num):
    slot_ranges = {
        "high": (0.9, 1.0),
        "mid": (0.75, 0.9),
        "low": (0.5, 0.75)
    }
    allowed_difficulties_range = {
        "易": ["易", "中"],
        "中": ["中", "难"],
        "难": ["难"]
    }
    left, right = slot_ranges[slot]
    done_set = get_done_questions(db, student_id)
    current_difficulty = get_difficulty(db, question_id)
    allowed_difficulties = allowed_difficulties_range[current_difficulty]

    faiss_service = FaissService(dim=768)
    index_size = faiss_service.index.ntotal
    vector = faiss_service.get_vector_by_id(question_id)

    # print(f"[DEBUG] question_id={question_id}, vector shape={vector.shape}, index_size={index_size}")

    k = 20
    difficulty_cache = {}
    while True:
        ids, scores = faiss_service.search_vector(vector, k=k)
        # print(f"[DEBUG] k={k}, ids={ids}, scores={scores}")  # 打印检索到的 ID 和相似度
        candidates = []
        for qid, score in zip(ids, scores):
            # 排除自己
            if qid == question_id:
                continue
            # 相似度过滤
            if not (left <= score <= right):
                # print(f"[DEBUG] qid={qid} score={score} 不在 {left}-{right} 范围内")
                continue
            # 学生是否做过
            if qid in done_set:
                # print(f"[DEBUG] qid={qid} 已完成")
                continue
            # 难度是否符合
            if qid in difficulty_cache:
                q_difficulty = difficulty_cache.get(qid)
            else:
                q_difficulty = get_difficulty(db, qid)
                difficulty_cache[qid] = q_difficulty
            if q_difficulty not in allowed_difficulties:
                # print(f"[DEBUG] qid={qid} 难度 {q_difficulty} 不允许")
                continue
            candidates.append((qid, score))

        # print(f"[DEBUG] 当前 candidates={candidates}")

        if len(candidates) >= expect_num:
            candidates.sort(key=lambda x: x[1], reverse=True)
            candidates = [(int(qid), float(score)) for qid, score in candidates]
            return candidates[:expect_num]
        if k >= index_size:
            candidates.sort(key=lambda x: x[1], reverse=True)
            candidates = [(int(qid), float(score)) for qid, score in candidates]
            return candidates
        # print(f"[DEBUG] 检索范围大小是：{k}")
        k = min(k * 2, index_size)

