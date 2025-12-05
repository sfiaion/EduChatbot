import random
from datetime import datetime, timedelta
from sqlalchemy import text
from faker import Faker
from app.db.session import SessionLocal
from sqlalchemy.orm import Session

import sys
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

fake = Faker("zh_CN")

# ======================
# ⚙️ 配置（你只需确认 knowledge_node_id 范围）
# ======================
# 假设你的 73 个知识节点 id 是 1~73（如果不是，改这里！）
KNOWLEDGE_NODE_IDS = list(range(1, 74))

ERROR_TYPE_WEIGHTS = {
    "knowledge": 5,
    "calculation": 3,
    "misreading": 2,
    "logic": 2,
    "method": 1,
}

def mock_error_analysis():
    db: Session = SessionLocal() # ← 直接用你的 session，自动连 SQLite/PG/MySQL
    try:
        # 🔥 清空表（SQLite 兼容写法）
        db.execute(text("DELETE FROM error_analysis"))
        # 重置自增 ID（SQLite）
        try:
            db.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'error_analysis'"))
        except:
            pass
        db.commit()
        print("🧹 已清空 error_analysis 表")

        # 📅 时间范围：最近7天
        start_date = datetime(2025, 11, 26)
        end_date = datetime(2025, 12, 2)

        records = []
        submission_id = 10000

        for _ in range(5000):
            node_id = random.choices(
                KNOWLEDGE_NODE_IDS,
                weights=[10 if i < 10 else 1 for i in range(len(KNOWLEDGE_NODE_IDS))],
                k=1
            )[0]

            error_type = random.choices(
                list(ERROR_TYPE_WEIGHTS.keys()),
                weights=list(ERROR_TYPE_WEIGHTS.values()),
                k=1
            )[0]

            analysis = random.choice([
                f"学生对「知识点#{node_id}」的理解存在偏差，建议复习前置内容。",
                f"混淆了{fake.word()}与{fake.word()}的概念，需强化辨析。",
                f"典型的知识性错误，反映出基础不牢。",
                f"未掌握核心公式推导过程，导致应用失败。",
                f"对题目条件限制理解不足，属于概念性疏漏。",
            ])

            knowledge_node_id = node_id if error_type == "knowledge" else None

            created_at = start_date + timedelta(
                days=random.randint(0, 6),
                hours=random.randint(8, 20),
                minutes=random.randint(0, 59)
            )

            records.append({
                "submission_id": submission_id,
                "error_type": error_type,
                "analysis": analysis,
                "knowledge_node_id": knowledge_node_id,
                "created_at": created_at
            })
            submission_id += 1

        # 🚀 批量插入（用你项目的 ORM 方式，最安全）
        from app.models import ErrorAnalysis  # ← 替换成你的模型名！
        db.bulk_insert_mappings(ErrorAnalysis, records)
        db.commit()

        print(f"✅ 成功插入 {len(records)} 条 error_analysis 数据！")
        print("💡 提示：知识点错误集中在 node_id 1~10，断点分析时会高亮它们！")

    except Exception as e:
        print(f"❌ 出错了: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    mock_error_analysis()