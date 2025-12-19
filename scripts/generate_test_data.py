import sys
import os
import random
from datetime import datetime, timedelta

# Add parent dir to sys.path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, Teacher, Student, Class
from app.models.question import Question, Assignment, StudentSubmission, ErrorAnalysis
from app.core.security import get_password_hash

def generate_test_data():
    db: Session = SessionLocal()
    try:
        print("Starting test data generation...")

        # 1. Ensure Teacher exists first (Class needs teacher_id)
        teacher_user = db.query(User).filter(User.username == "teacher_test").first()
        if not teacher_user:
            teacher_user = User(
                username="teacher_test",
                role="teacher",
                password_hash=get_password_hash("123456"),
                email="teacher@test.com",
                nickname="Mr. Anderson"
            )
            db.add(teacher_user)
            db.commit()
            db.refresh(teacher_user)
            
            teacher_profile = Teacher(user_id=teacher_user.id, name="Mr. Anderson")
            db.add(teacher_profile)
            db.commit()
            db.refresh(teacher_profile)
            print("Created Teacher: Mr. Anderson")
        else:
            teacher_profile = teacher_user.teacher

        # 2. Ensure Class exists
        clazz = db.query(Class).filter(Class.name == "Class 101").first()
        if not clazz:
            clazz = Class(name="Class 101", teacher_id=teacher_profile.id)
            db.add(clazz)
            db.commit()
            db.refresh(clazz)
            print(f"Created Class: {clazz.name}")

        # 3. Create Students
        students = []
        for i in range(1, 6):
            username = f"student_{i}"
            user = db.query(User).filter(User.username == username).first()
            if not user:
                user = User(
                    username=username,
                    role="student",
                    password_hash=get_password_hash("123456"),
                    email=f"student{i}@test.com",
                    nickname=f"Student {i}"
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                student = Student(
                    user_id=user.id, 
                    student_number=f"S{1000+i}", 
                    name=f"Student {i}", 
                    class_id=clazz.id
                )
                db.add(student)
                db.commit()
                db.refresh(student)
                students.append(student)
                print(f"Created Student: {student.name}")
            else:
                students.append(user.student)

        # 4. Create Questions
        questions = []
        difficulties = ['easy', 'medium', 'hard']
        tags = ['Algebra', 'Geometry', 'Calculus', 'Statistics']
        
        for i in range(1, 6):
            q_text = f"Solve problem #{i}: Calculate the integral of x^{i} dx"
            q = db.query(Question).filter(Question.normalized_question == q_text).first()
            if not q:
                q = Question(
                    question=q_text,
                    normalized_question=q_text,
                    answer=f"x^{i+1}/{i+1} + C",
                    knowledge_tag=random.choice(tags),
                    difficulty_tag=random.choice(difficulties)
                )
                db.add(q)
                db.commit()
                db.refresh(q)
            questions.append(q)
        print(f"Ensured {len(questions)} questions exist.")

        # 5. Create Assignments
        # Assignment 1: Completed
        assign1 = db.query(Assignment).filter(Assignment.title == "Midterm Review").first()
        if not assign1:
            assign1 = Assignment(
                title="Midterm Review",
                teacher_id=teacher_profile.id,
                class_id=clazz.id,
                deadline=datetime.now() - timedelta(days=1),
                assigned_student_ids=[s.id for s in students],
                assigned_question_ids=[q.id for q in questions]
            )
            db.add(assign1)
            db.commit()
            db.refresh(assign1)
            print("Created Assignment: Midterm Review")

        # Assignment 2: Ongoing
        assign2 = db.query(Assignment).filter(Assignment.title == "Final Prep").first()
        if not assign2:
            assign2 = Assignment(
                title="Final Prep",
                teacher_id=teacher_profile.id,
                class_id=clazz.id,
                deadline=datetime.now() + timedelta(days=5),
                assigned_student_ids=[s.id for s in students],
                assigned_question_ids=[q.id for q in questions[:3]]
            )
            db.add(assign2)
            db.commit()
            print("Created Assignment: Final Prep")

        # 6. Generate Submissions for Assignment 1
        # Clear existing submissions for this assignment to avoid duplicates/conflicts in test
        # (Optional, but good for idempotent runs. Skipping for safety, just checking existence)
        
        print("Generating submissions...")
        error_types = ['calculation', 'knowledge', 'logic']
        
        for student in students:
            # Simulate each student answering each question
            for q in questions:
                existing_sub = db.query(StudentSubmission).filter(
                    StudentSubmission.assignment_id == assign1.id,
                    StudentSubmission.student_id == student.id,
                    StudentSubmission.question_id == q.id
                ).first()
                
                if not existing_sub:
                    is_correct = random.random() > 0.4 # 60% pass rate
                    sub = StudentSubmission(
                        question_id=q.id,
                        student_id=student.id,
                        assignment_id=assign1.id,
                        student_answer="Correct Answer" if is_correct else "Wrong Answer",
                        is_correct=is_correct
                    )
                    db.add(sub)
                    db.commit()
                    db.refresh(sub)
                    
                    if not is_correct:
                        # Add error analysis
                        err = ErrorAnalysis(
                            submission_id=sub.id,
                            error_type=random.choice(error_types),
                            analysis="Simulated AI Analysis: Student made a mistake here."
                        )
                        db.add(err)
                        db.commit()
        
        print("Test data generation complete!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_test_data()
