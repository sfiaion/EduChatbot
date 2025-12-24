from app.db.session import SessionLocal
from app.models.question import ErrorAnalysis, StudentSubmission
from sqlalchemy import func

def check_db():
    s = SessionLocal()
    try:
        count = s.query(ErrorAnalysis).count()
        print(f"ErrorAnalysis Count: {count}")
        
        if count > 0:
            last = s.query(ErrorAnalysis).order_by(ErrorAnalysis.id.desc()).first()
            print(f"Last Error: ID={last.id}, NodeID={last.knowledge_node_id}, SubID={last.submission_id}")
            
        subs = s.query(StudentSubmission).count()
        print(f"Submissions Count: {subs}")
        
    finally:
        s.close()

if __name__ == "__main__":
    check_db()
