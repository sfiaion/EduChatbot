import re
import os
from ..ml.classify_questions_from_teachers import auto_labels
from ..utils.convert_file import parse_document
from ..utils.manage_dir import new_task_tmp_dir, clear_dir
from ..crud.question import create_question
from sqlalchemy.orm import Session
from fastapi import UploadFile
from ..models import Question

def upload_questions(file: UploadFile, db: Session, teacher_id: int):
    tmp_dir = new_task_tmp_dir()
    input_path = os.path.join(tmp_dir, file.filename)
    try:
        with open(input_path, "wb") as f:
            f.write(file.file.read())
        file_to_questions(input_path, db, tmp_dir)
        return {"status": "success"}
    except Exception as e:
        print("Error during upload:", e)
        return {"error": str(e)}
    finally:
        clear_dir(tmp_dir)



def file_to_questions(path, db: Session, tmp_dir: str):
    final_text = parse_document(path, tmp_dir)
    final_list = [line.strip() for line in final_text.split("\n") if line.strip()]

    question_list = []
    normalized_question_list = []
    answer_list = []

    for i, string in enumerate(final_list):
        if i % 2 == 0:
            question_list.append(string)
            normalized_question_list.append(normalize_text(string))
        else:
            answer_list.append(string)

    # 清空表
    # db.query(Question).delete()
    # db.commit()
    for i, question in enumerate(question_list):
        types, properties, difficulty = auto_labels(question_list[i], answer_list[i])
        # print(types)
        # print(properties)
        # print(difficulty)
        db_question = create_question(
            db,
            question_list[i],
            normalized_question_list[i],
            answer_list[i],
            types,
            properties,
            difficulty
        )

        # print(db_question.question)
        # print(db_question.answer)
        # print(db_question.knowledge_tag["types"])
        # print(db_question.knowledge_tag["properties"])
        # print(db_question.difficulty_tag)



def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\s+', '', text)               # 去掉所有空白
    text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)  # 去掉符号，仅保留中英文与数字
    return text