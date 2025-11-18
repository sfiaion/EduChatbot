from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, JSON, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    normalized_question = Column(String, nullable=False, unique=True)
    answer = Column(String, nullable=False)
    knowledge_tag = Column(JSON, nullable=False)
    difficulty_tag = Column(String, nullable=False)  # 'easy', 'medium', 'hard'
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    submissions = relationship("StudentSubmission", back_populates="question")

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    assigned_student_ids = Column(JSON, nullable=False)  # List[int]
    assigned_question_ids = Column(JSON, nullable=False)  # List[int]
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    teacher = relationship("Teacher", back_populates="assignments")

class StudentSubmission(Base):
    __tablename__ = "student_submissions"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=True)
    student_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=True, default=None)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    question = relationship("Question", back_populates="submissions")
    student = relationship("Student", back_populates="submissions")
    error_analysis = relationship("ErrorAnalysis", back_populates="submission", uselist=False)


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id = Column(Integer, primary_key=True, index=True)
    function_type = Column(String, nullable=True)
    function_property = Column(String, nullable=True)
    name = Column(String, unique=True, nullable=False)
    content = Column(String, nullable=False)

    # Relationships
    error_analyses = relationship("ErrorAnalysis", back_populates="knowledge_node")


class ErrorAnalysis(Base):
    __tablename__ = "error_analysis"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("student_submissions.id"), nullable=False, unique=True)
    error_type = Column(String, nullable=False)  # knowledge/calculation/misreading/logic/method
    analysis = Column(String, nullable=False)
    knowledge_node_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    submission = relationship("StudentSubmission", back_populates="error_analysis")
    knowledge_node = relationship("KnowledgeNode", back_populates="error_analyses")