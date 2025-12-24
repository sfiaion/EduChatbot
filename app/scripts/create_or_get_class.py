import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app"))

from db.session import SessionLocal
from models.user import Class, Teacher, User


def main():
    if len(sys.argv) < 3:
        print("USAGE: python -m app.scripts.create_or_get_class <teacher_username> <class_name>")
        return
    teacher_username = sys.argv[1]
    class_name = sys.argv[2]
    s = SessionLocal()
    try:
        teacher = s.query(Teacher).join(User, Teacher.user_id == User.id)\
            .filter(User.username == teacher_username).first()
        if not teacher:
            print("ERROR: teacher not found:", teacher_username)
            return
        c = s.query(Class).filter(Class.name == class_name, Class.teacher_id == teacher.id).first()
        if not c:
            c = Class(name=class_name, teacher_id=teacher.id)
            s.add(c)
            s.commit()
            s.refresh(c)
        print(f"CLASS_ID={c.id}")
    finally:
        s.close()


if __name__ == "__main__":
    main()
