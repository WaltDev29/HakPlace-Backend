from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Float, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    meal_id = Column(Integer, ForeignKey("meals.meal_id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(10), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    rating = Column(Float, nullable=False)
    review_comment = Column(Text)
    photo_url = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('meal_id', 'student_id'),
    )

    meal = relationship("Meal", back_populates="reviews")
    student = relationship("Student", back_populates="reviews")
