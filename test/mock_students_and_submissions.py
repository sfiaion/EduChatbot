import random
from datetime import datetime, timedelta
from sqlalchemy import text
from faker import Faker
from app.db.session import SessionLocal
from sqlalchemy.orm import Session
import sys
import pathlib

# 🔍 自动定位项目根目录（不硬编码绝对路径！）
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

fake = Faker("zh_CN")

# ======================
# ⚙️ 配置区（你只需改这里！）
# ======================
CLASSES = [
    {"id": 1, "name": "高三(1)班"},
    {"id": 2, "name": "高三(2)班"},
    {"id": 3, "name": "高三(3)班"},
]  # 你可以增减班级；class_id 必须与你 filter 中用的一致（如 class_id=1）

STUDENTS_PER_CLASS = 40  # 每班人数
SUBMISSIONS_PER_STUDENT = 10  # 平均每人多少次作答（总 submission ≈ class_num * per_class * per_stu）

# 时间范围——与你 error_analysis 的时间对齐！
START_DATE = datetime(2025, 11, 26)
END_DATE = datetime(2025, 12, 2)

# 错误率：控制 is_correct=False 的比例（0.45 ≈ 45% 错题）
ERROR_RATE = 0.45

# ⚠️ 注意：你之前的 error_analysis 用了 submission_id 从 10000 开始 → 我们也从 10000 起
START_SUBMISSION_ID = 10000
START_STUDENT_ID = 1  # 假设学生 id 从 1 开始（可改）

# ======================
# 📝 准备数据
# ======================

def mock_students_and_submissions():
    db: Session = SessionLocal()
    try:
        # 🔥 清空表（兼容 SQLite / 其他）
        for table in ["student_submissions", "students"]:
            db.execute(text(f"DELETE FROM {table}"))
            try:
                # SQLite 自增重置
                db.execute(text(f"UPDATE sqlite_sequence SET seq = 0 WHERE name = '{table}'"))
            except Exception:
                pass
        db.commit()
        print("🧹 已清空 students 和 student_submissions 表")

        # 🧑‍🎓 生成学生
        students = []
        student_id = START_STUDENT_ID
        for cls in CLASSES:
            for i in range(1, STUDENTS_PER_CLASS + 1):
                # 学号：班级缩写+序号，如 G3-1-01
                class_short = cls["name"].replace("(", "-").replace(")", "")
                student_number = f"{class_short}-{i:02d}"
                students.append({
                    "id": student_id,
                    "user_id": student_id,  # 简单映射（若你有 user 表再扩展）
                    "student_number": student_number,
                    "name": fake.name(),
                    "class_id": cls["id"],
                })
                student_id += 1

        # 📤 插入学生
        from app.models import Student  # ← 请确认你的模型类名！
        db.bulk_insert_mappings(Student, students)
        db.commit()
        print(f"✅ 成功插入 {len(students)} 名学生")

        # 📝 生成作答记录
        submissions = []
        submission_id = START_SUBMISSION_ID
        question_ids_pool = list(range(1, 101))  # 假设有 100 道题，id 1~100

        for student in students:
            # 每人生成若干次作答
            n_submissions = random.randint(
                int(SUBMISSIONS_PER_STUDENT * 0.8),
                int(SUBMISSIONS_PER_STUDENT * 1.2)
            )
            for _ in range(n_submissions):
                # 随机时间（在范围内）
                delta_days = (END_DATE - START_DATE).days
                random_time = START_DATE + timedelta(
                    days=random.randint(0, delta_days),
                    hours=random.randint(8, 21),
                    minutes=random.randint(0, 59),
                    seconds=random.randint(0, 59)
                )

                # 随机题目
                question_id = random.choice(question_ids_pool)

                # 随机是否正确（按 ERROR_RATE 错误）
                is_correct = random.random() > ERROR_RATE

                # 学生乱答内容（简单模拟）
                student_answer = fake.sentence(nb_words=5) if not is_correct else "答案正确"

                submissions.append({
                    "id": submission_id,
                    "question_id": question_id,
                    "student_id": student["id"],
                    "assignment_id": random.choice([101, 102, 103, None]),  # 可能无作业归属
                    "student_answer": student_answer,
                    "is_correct": is_correct,
                    "created_at": random_time,
                })
                submission_id += 1

        # 📤 插入作答
        from app.models import StudentSubmission  # ← 请确认你的模型类名！
        db.bulk_insert_mappings(StudentSubmission, submissions)
        db.commit()
        print(f"✅ 成功插入 {len(submissions)} 条学生作答记录")

        # 🔗 验证关联：统计各班错误作答数（方便你后续测试）
        print("\n📊 各班错误作答统计（is_correct=False）：")
        error_counts = {}
        for cls in CLASSES:
            cnt = sum(
                1 for s in submissions
                if any(stu["id"] == s["student_id"] and stu["class_id"] == cls["id"] for stu in students)
                and s["is_correct"] is False
            )
            error_counts[cls["id"]] = cnt
            print(f"  班级 {cls['name']} (id={cls['id']}): {cnt} 次错误")

        # ✅ 提示
        print("\n💡 提示：")
        print(f"   - 学生 ID 范围：{students[0]['id']} ~ {students[-1]['id']}")
        print(f"   - submission_id 范围：{START_SUBMISSION_ID} ~ {submission_id - 1}")
        print(f"   - 时间范围：{START_DATE.date()} 至 {END_DATE.date()}")
        print("   - 可直接与你已生成的 error_analysis 数据 JOIN（submission_id 对齐！）")

    except Exception as e:
        print(f"❌ 出错了: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🎯 开始生成测试学生与作答数据……")
    mock_students_and_submissions()