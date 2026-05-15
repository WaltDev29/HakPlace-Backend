from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, Table, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base

# Association table for Meal and Food
meal_foods = Table(
    'meal_foods',
    Base.metadata,
    Column('meal_id', Integer, ForeignKey('meals.meal_id', ondelete="CASCADE"), primary_key=True),
    Column('food_id', Integer, ForeignKey('foods.food_id', ondelete="CASCADE"), primary_key=True)
)

class Meal(Base):
    __tablename__ = "meals"

    meal_id = Column(Integer, primary_key=True, autoincrement=True)
    served_date = Column(Date, nullable=False)
    meal_type = Column(String(20), nullable=False)
    avg_rating = Column(Numeric(3, 2), default=0.00)
    review_count = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint('served_date', 'meal_type'),
        CheckConstraint("meal_type IN ('조식', '중식', '석식')"),
    )

    foods = relationship("Food", secondary=meal_foods, back_populates="meals")
    reviews = relationship("Review", back_populates="meal", cascade="all, delete-orphan")

class Food(Base):
    __tablename__ = "foods"

    food_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)

    meals = relationship("Meal", secondary=meal_foods, back_populates="foods")
