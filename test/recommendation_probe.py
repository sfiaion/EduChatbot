import os
import sys
import pathlib
BASE = pathlib.Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.question import Question, StudentSubmission
from app.services.faiss_service import FaissService
def ensure_wrong_submission(db, student_id, question_id):
    sub = db.query(StudentSubmission).filter(
        StudentSubmission.student_id == student_id,
        StudentSubmission.question_id == int(question_id)
    ).first()
    if not sub:
        sub = StudentSubmission(
            assignment_id=9999,
            student_id=student_id,
            question_id=int(question_id),
            student_answer="",
            image_path=None,
            is_correct=False
        )
        db.add(sub)
    else:
        sub.is_correct = False
    db.commit()
def main(base_id: int | None = None):
    svc = FaissService(dim=768)
    ids = list(svc.id2vector.keys())
    if not ids:
        print("faiss empty")
        return
    if base_id is None:
        base_id = int(ids[0])
    db = SessionLocal()
    try:
        q = db.query(Question).filter(Question.id == base_id).first()
        if not q:
            print("question missing for id", base_id)
            return
        ensure_wrong_submission(db, 1, base_id)
    finally:
        db.close()
    client = TestClient(app)
    for slot in ["high", "mid", "low"]:
        resp = client.post(f"/api/problems/{base_id}/recommendation", json={
            "question_id": base_id,
            "student_id": 2,
            "slot": slot,
            "expect_num": 5
        })
        print("slot:", slot, "status:", resp.status_code)
        if resp.status_code == 200:
            print(resp.json())
if __name__ == "__main__":
    import sys
    arg = None
    if len(sys.argv) > 1:
        try:
            arg = int(sys.argv[1])
        except Exception:
            arg = None
    main(arg)
