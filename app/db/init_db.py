# app/db/init_db.py
import os
import sys
import pathlib

# 将 app/ 目录加入 Python 路径（确保能导入 core, models）
APP_DIR = pathlib.Path(__file__).parent.parent  # app/ 目录
sys.path.insert(0, str(APP_DIR))

from core.config import settings
from models import Base

if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

def init_db():
    from sqlalchemy import create_engine
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    print(f"✅ 数据库初始化成功！使用数据库: {settings.database_url}")

if __name__ == "__main__":
    init_db()