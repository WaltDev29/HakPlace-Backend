from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

class FoodSchema(BaseModel):
    food_id: int = Field(..., example=1)
    name: str = Field(..., example="제육볶음")

    class Config:
        from_attributes = True

class MealSchema(BaseModel):
    meal_id: int = Field(..., example=101)
    served_date: datetime.date = Field(..., example="2024-05-13")
    meal_type: str = Field(..., example="중식")
    avg_rating: float = Field(..., example=4.5)
    review_count: int = Field(..., example=12)
    foods: List[str] = Field(..., example=["밥", "국", "제육볶음", "김치"])

    class Config:
        from_attributes = True

class DailyMeals(BaseModel):
    served_date: datetime.date = Field(..., example="2024-05-13", alias="date")
    breakfast: Optional[MealSchema] = None
    lunch: Optional[MealSchema] = None
    dinner: Optional[MealSchema] = None

    class Config:
        populate_by_name = True

class WeeklyMeals(BaseModel):
    week_meals: List[DailyMeals]
