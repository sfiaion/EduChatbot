from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ErrorType(str, Enum):
    KNOWLEDGE = "knowledge"          # 知识点错误
    CALCULATION = "calculation"      # 计算错误
    MISREADING = "misreading"        # 审题错误
    LOGIC = "logic"                  # 逻辑错误
    METHOD = "method"                # 方法错误

class CorrectionRequest(BaseModel):
    question_id: int
    student_answer: str

class CorrectionResponse(BaseModel):
    is_correct: bool
    message: Optional[str] = None      # 正确时填充
    error_type: Optional[ErrorType] = None   # 错误时填充
    analysis: Optional[str] = None     # 错误时填充
    knowledge_node_id: Optional[int] = None
    knowledge_node_id: Optional[int] = None
    knowledge_id: Optional[int] = None
