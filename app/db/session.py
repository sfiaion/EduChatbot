# db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from ..core.config import settings  # ← 导入配置实例

# 使用配置中的 DATABASE_URL
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # 仅 SQLite 需要
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()