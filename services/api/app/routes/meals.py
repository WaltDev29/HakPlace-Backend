from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Meal, Food
from app.schemas.meal import DailyMeals, MealSchema, WeeklyMeals
from datetime import date, timedelta
from typing import List

router = APIRouter()

def format_meal(meal: Meal) -> MealSchema:
    if not meal:
        return None
    return MealSchema(
        meal_id=meal.meal_id,
        served_date=meal.served_date,
        meal_type=meal.meal_type,
        avg_rating=float(meal.avg_rating),
        review_count=meal.review_count,
        foods=[food.name for food in meal.foods]
    )

@router.get("/today", response_model=DailyMeals, summary="금일 식단 조회", description="특정 날짜(기본값은 오늘)의 조식, 중식, 석식 메뉴를 모두 조회합니다.")
def get_today_meals(target_date: date = None, db: Session = Depends(get_db)):
    if not target_date:
        target_date = date.today()
    
    meals = db.query(Meal).filter(Meal.served_date == target_date).all()
    
    res = DailyMeals(date=target_date)
    for m in meals:
        formatted = format_meal(m)
        if m.meal_type == '조식':
            res.breakfast = formatted
        elif m.meal_type == '중식':
            res.lunch = formatted
        elif m.meal_type == '석식':
            res.dinner = formatted
            
    return res

@router.get("/weekly", response_model=WeeklyMeals, summary="주간 식단 조회", description="이번 주 월요일부터 금요일까지의 모든 식단 정보를 조회합니다.")
def get_weekly_meals(db: Session = Depends(get_db)):
    # 이번 주 월요일부터 금요일까지 조회
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    
    meals = db.query(Meal).filter(
        Meal.served_date >= monday,
        Meal.served_date <= friday
    ).order_by(Meal.served_date, Meal.meal_id).all()
    
    # 날짜별로 그룹화
    days_map = {}
    for i in range(5):
        d = monday + timedelta(days=i)
        days_map[d] = DailyMeals(date=d)
        
    for m in meals:
        formatted = format_meal(m)
        day_meal = days_map.get(m.served_date)
        if day_meal:
            if m.meal_type == '조식':
                day_meal.breakfast = formatted
            elif m.meal_type == '중식':
                day_meal.lunch = formatted
            elif m.meal_type == '석식':
                day_meal.dinner = formatted
                
    return WeeklyMeals(week_meals=list(days_map.values()))
