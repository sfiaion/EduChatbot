from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI
from app.api import correction, ocr
from app.api.graph import router as graph_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="EduChatbot Backend")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(correction.router, prefix="/api/correction", tags=["Correction"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR"])
app.include_router(graph_router, prefix="/api")