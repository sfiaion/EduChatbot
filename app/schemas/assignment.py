from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class AssignmentBase(BaseModel):
    title: str

class AssignmentCreate(AssignmentBase):
    # Optional: Can be empty when creating via upload
    teacher_id: int
    class_id: int
    deadline: Optional[datetime] = None
    assigned_student_ids: List[int] = []
    assigned_question_ids: List[int] = []

class AssignmentRead(AssignmentBase):
    id: int
    teacher_id: int
    class_id: int
    deadline: Optional[datetime]
    assigned_student_ids: List[int]
    assigned_question_ids: List[int]
    created_at: datetime
    is_submitted: Optional[bool] = False

    # Support Pydantic v2 (use 'orm_mode = True' if on v1)
    model_config = ConfigDict(from_attributes=True)

class AssignmentStats(BaseModel):
    total_students: int
    total_questions: int
