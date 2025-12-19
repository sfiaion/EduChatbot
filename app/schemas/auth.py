from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str # student, teacher
    name: str
    # Student specific
    student_number: Optional[str] = None
    class_id: Optional[int] = None
    
class UserResponse(BaseModel):
    id: int
    username: str
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    nickname: Optional[str] = None
    role: str
    name: str
    student_id: Optional[int] = None
    teacher_id: Optional[int] = None
    class_name: Optional[str] = None
    teacher_name: Optional[str] = None
    classes: Optional[list[str]] = None

    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
