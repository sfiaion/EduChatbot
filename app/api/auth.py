from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.db.session import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User, Student, Teacher
from app.schemas.auth import UserCreate, Token, UserResponse, UserProfileUpdate
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    # Create User
    user = User(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role,
        nickname=user_in.name # Default nickname to name
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create Profile
    if user_in.role == "student":
        student = Student(
            user_id=user.id,
            name=user_in.name,
            student_number=user_in.student_number or user_in.username,
            class_id=user_in.class_id 
        )
        db.add(student)
    elif user_in.role == "teacher":
        teacher = Teacher(
            user_id=user.id,
            name=user_in.name
        )
        db.add(teacher)
    
    db.commit()
    db.refresh(user)
    
    return _build_user_response(user)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Login with username
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(subject=user.id, role=user.role)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return _build_user_response(current_user)

@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if profile_in.nickname is not None:
        current_user.nickname = profile_in.nickname
    if profile_in.phone is not None:
        # Check uniqueness if phone is provided
        if profile_in.phone:
            existing_phone = db.query(User).filter(User.phone == profile_in.phone).first()
            if existing_phone and existing_phone.id != current_user.id:
                 raise HTTPException(status_code=400, detail="Phone already in use")
        current_user.phone = profile_in.phone
    if profile_in.email is not None:
        current_user.email = profile_in.email
    if profile_in.avatar is not None:
        current_user.avatar = profile_in.avatar
        
    db.commit()
    db.refresh(current_user)
    return _build_user_response(current_user)

def _build_user_response(user: User) -> UserResponse:
    name = ""
    class_name = None
    teacher_name = None
    classes = []

    if user.student:
        name = user.student.name
        if user.student.clazz:
            class_name = user.student.clazz.name
            if user.student.clazz.teacher:
                teacher_name = user.student.clazz.teacher.name
    elif user.teacher:
        name = user.teacher.name
        if user.teacher.classes:
            classes = [c.name for c in user.teacher.classes]
    
    return UserResponse(
        id=user.id,
        username=user.username,
        phone=user.phone,
        email=user.email,
        avatar=user.avatar,
        nickname=user.nickname,
        role=user.role,
        name=name,
        student_id=user.student.id if user.student else None,
        teacher_id=user.teacher.id if user.teacher else None,
        class_name=class_name,
        teacher_name=teacher_name,
        classes=classes
    )
