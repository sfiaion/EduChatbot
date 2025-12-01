from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI
from app.api import correction, submissions, graph, problems
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="EduChatbot Backend")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(correction.router, prefix="/api", tags=["Correction"]) # 自动批改
app.include_router(problems.router, prefix="/api", tags=["Problems"]) # 教师上传题目，错题推荐
app.include_router(submissions.router, prefix="/api", tags=["Submissions"]) # 学生提交答案
app.include_router(graph.router, prefix="/api", tags=["KnowledgeGraph"]) # 知识图谱