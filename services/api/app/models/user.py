from sqlalchemy import Column, String, Date, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Student(Base):
    __tablename__ = "students"

    student_id = Column(String(10), primary_key=True)
    name = Column(String(20), nullable=False)
    birth_date = Column(Date)
    phone_number = Column(String(15))
    gender = Column(Enum('F', 'M'))

    account = relationship("Account", back_populates="student", uselist=False, cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="student", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "accounts"

    student_id = Column(String(10), ForeignKey("students.student_id", ondelete="CASCADE"), primary_key=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_login = Column(TIMESTAMP, nullable=True)

    student = relationship("Student", back_populates="account")
