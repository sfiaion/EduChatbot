import os
import uuid
import shutil

BASE_TMP_DIR = "tmp"


def new_task_tmp_dir() -> str:
    if not os.path.exists(BASE_TMP_DIR):
        os.makedirs(BASE_TMP_DIR)
    task_id = f"task_{uuid.uuid4().hex}"
    task_dir = os.path.join(BASE_TMP_DIR, task_id)
    os.makedirs(task_dir)
    return task_dir


def clear_dir(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)
