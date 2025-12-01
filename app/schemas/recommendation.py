from pydantic import BaseModel, Field
from typing import List, Literal

class RecommendedItem(BaseModel):
    id: int
    score: float

class RecommendationRequest(BaseModel):
    question_id: int
    student_id: int
    slot: Literal["high", "mid", "low"] = "high"
    expect_num: int = Field(5, ge=1, le=10)

class RecommendationResponse(BaseModel):
    base_question_id: int
    slot: str
    expected: int
    found: int
    items: List[RecommendedItem]