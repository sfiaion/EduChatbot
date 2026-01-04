# main.py
from dotenv import load_dotenv
import os
import pathlib

load_dotenv()

from fastapi import FastAPI
from app.db.init_db import init_db
from app.api import correction, submissions, graph_strcture, graph_analysis, problems, teacher, knowledge, chat, assignments, practice, wrongbook, auth, upload, classes, notifications
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(title="EduChatbot Backend")
init_db()
STATIC_DIR = pathlib.Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(correction.router, prefix="/api", tags=["Correction"]) # 自动批改
app.include_router(problems.router, prefix="/api", tags=["Problems"]) # 教师上传题目，错题推荐
app.include_router(submissions.router, prefix="/api", tags=["Submissions"]) # 学生提交答案
app.include_router(graph_strcture.router, prefix="/api", tags=["KnowledgeGraph"]) # 知识图谱
app.include_router(graph_analysis.router, prefix="/api", tags=["KnowledgeGraph"]) # 知识图谱
app.include_router(teacher.router, prefix="/api", tags=["Teacher"])
app.include_router(knowledge.router, prefix="/api", tags=["Knowledge"])
app.include_router(assignments.router, prefix="/api", tags=["Assignments"])
app.include_router(practice.router, prefix="/api", tags=["Practice"])
app.include_router(wrongbook.router, prefix="/api", tags=["Wrongbook"])
app.include_router(classes.router, prefix="/api", tags=["Classes"])
app.include_router(notifications.router, prefix="/api", tags=["Notifications"])



