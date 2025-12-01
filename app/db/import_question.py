import pandas as pd
from sqlalchemy.orm import Session
from ..models import Question  # 你的 SQLAlchemy 模型
import re
import ast
import sys
import pathlib
import pandas as pd
from sqlalchemy import text
from app.db.session import SessionLocal

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

EXCEL_PATH = PROJECT_ROOT / "docs" / "项目题库.xlsx"
SHEET_NAME = "Sheet1"

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\s+', '', text)  # 去掉空白
    text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)  # 去掉符号
    text = re.sub(r'_+', '', text)
    return text


def clean_list(text):
    """
    将 "指数函数, 对数函数, 幂函数" → ["指数函数", "对数函数", "幂函数"]
    """
    if text is None:
        return []
    if isinstance(text, list):
        return text
    if isinstance(text, str):
        parts = [t.strip() for t in text.split(",") if t.strip()]
        return parts
    return []

def load_questions_from_csv():
    """
    加载 CSV，如果是 Excel 改成 pd.read_excel(path)
    """
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, dtype=str)  # 如果是 Excel → pd.read_excel(path)

    required_cols = ["题目", "答案和解析", "函数类型", "函数性质", "难度等级"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"缺少列：{col}")

    return df


def insert_questions_to_db():
    db: Session = SessionLocal()
    try:
        db.query(Question).delete()
        db.commit()
        db.expire_all()

        df = load_questions_from_csv()

        inserted = 0
        skipped = 0

        seen_normalized = set()

        for idx, row in df.iterrows():
            question = re.sub(r'\s*\|\|\s*', '\n', str(row["题目"]).strip())
            answer = re.sub(r'\s*\|\|\s*', '\n', str(row["答案和解析"]).strip())
            normalized_question = normalize_text(question)

            if normalized_question in seen_normalized:
                skipped += 1
                continue

            existing = db.query(Question).filter(
                Question.normalized_question == normalized_question
            ).first()

            if existing:
                skipped += 1
                continue

            seen_normalized.add(normalized_question)

            types = clean_list(row["函数类型"])
            properties = clean_list(row["函数性质"])
            difficulty = str(row["难度等级"]).strip()

            db_question = Question(
                question=question,
                normalized_question=normalized_question,
                answer=answer,
                knowledge_tag={"types": types, "properties": properties},
                difficulty_tag=difficulty,
            )

            db.add(db_question)
            inserted += 1

        db.commit()
        print(f"插入成功 {inserted} 条，跳过 {skipped} 条（重复）")

    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    insert_questions_to_db()
