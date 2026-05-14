import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.models import Statistic
from app.schemas.statistic import StatisticResponse, StatisticList, FoodRatingList, WeeklyGraphData, MonthlyGraphData
from app.utils.date_utils import get_monday_date
from typing import Optional, List
from datetime import datetime, timedelta
import calendar

router = APIRouter()

def parse_ai_comment(comment: Optional[str]):
    if not comment:
        return None
    try:
        return json.loads(comment)
    except:
        return comment

@router.get("/", response_model=StatisticList, summary="전체 통계 목록 조회", description="주차별 또는 월별로 생성된 모든 AI 분석 통계 데이터를 조회합니다.")
def get_statistics(
    period_type: Optional[str] = None, # WEEKLY, MONTHLY
    db: Session = Depends(get_db)
):
    query = db.query(Statistic)
    if period_type:
        query = query.filter(Statistic.period_type == period_type)
        
    stats = query.order_by(Statistic.period_value.desc()).all()
    
    res = []
    for s in stats:
        res.append(StatisticResponse(
            stat_id=s.stat_id,
            period_type=s.period_type,
            period_value=s.period_value,
            avg_rating=float(s.avg_rating) if s.avg_rating else None,
            ai_comment=parse_ai_comment(s.ai_comment),
            total_reviews=s.total_reviews,
            created_at=s.created_at
        ))
        
    return StatisticList(stats=res)

@router.get("/weekly", response_model=List[WeeklyGraphData], summary="주간 그래프 데이터 조회", description="특정 주차의 월~금 일별 평균 평점을 반환합니다.")
def get_weekly_graph_data(date: Optional[str] = None, db: Session = Depends(get_db)):
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).")
        
    monday_str = get_monday_date(dt)
    monday_dt = datetime.strptime(monday_str, "%Y-%m-%d")
    friday_dt = monday_dt + timedelta(days=4)

    # 일별 가중 평균 계산
    query = text("""
        SELECT served_date, SUM(avg_rating * review_count) / SUM(review_count) as daily_avg
        FROM meals
        WHERE served_date BETWEEN :start AND :end AND review_count > 0
        GROUP BY served_date
        ORDER BY served_date ASC
    """)
    res = db.execute(query, {"start": monday_dt.date(), "end": friday_dt.date()}).fetchall()
    
    day_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금"}
    data_dict = {str(row.served_date): float(row.daily_avg) for row in res}
    
    result = []
    for i in range(5):
        current_dt = monday_dt + timedelta(days=i)
        current_str = current_dt.strftime("%Y-%m-%d")
        result.append(WeeklyGraphData(
            date=current_str,
            label=day_map[i],
            avg_rating=round(data_dict[current_str], 1) if current_str in data_dict else None
        ))
    
    return result

@router.get("/monthly", response_model=List[MonthlyGraphData], summary="월간 그래프 데이터 조회", description="특정 월의 모든 주차별 평균 평점을 meals 데이터를 기반으로 실시간 집계합니다. 데이터가 없는 주차는 null로 반환됩니다.")
def get_monthly_graph_data(month: Optional[str] = None, db: Session = Depends(get_db)):
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    try:
        year, month_part = map(int, month.split("-"))
    except:
        raise HTTPException(status_code=400, detail="월 형식이 올바르지 않습니다 (YYYY-MM).")

    # 1. 해당 월의 모든 월요일 찾기
    num_days = calendar.monthrange(year, month_part)[1]
    mondays = []
    for day in range(1, num_days + 1):
        d = datetime(year, month_part, day)
        if d.weekday() == 0: # Monday
            mondays.append(d.strftime("%Y-%m-%d"))
    
    if not mondays:
        return []

    # 2. 해당 월의 모든 식단 데이터 가져오기 (가중 평균 계산용)
    start_date = mondays[0]
    last_monday_dt = datetime.strptime(mondays[-1], "%Y-%m-%d")
    end_date = (last_monday_dt + timedelta(days=6)).strftime("%Y-%m-%d")

    query = text("""
        SELECT served_date, avg_rating, review_count
        FROM meals
        WHERE served_date BETWEEN :start AND :end AND review_count > 0
    """)
    meals_res = db.execute(query, {"start": start_date, "end": end_date}).fetchall()
    
    # 3. 주차별(월요일 기준) 데이터 합산
    week_stats = {m: {"sum_rating": 0.0, "sum_count": 0} for m in mondays}

    for row in meals_res:
        meal_date = row.served_date
        # 해당 날짜의 월요일 계산
        monday_of_meal = meal_date - timedelta(days=meal_date.weekday())
        monday_str = monday_of_meal.strftime("%Y-%m-%d")
        
        if monday_str in week_stats:
            week_stats[monday_str]["sum_rating"] += float(row.avg_rating) * row.review_count
            week_stats[monday_str]["sum_count"] += row.review_count

    # 4. 결과 생성
    result = []
    for idx, monday in enumerate(mondays):
        stats = week_stats[monday]
        avg = round(stats["sum_rating"] / stats["sum_count"], 1) if stats["sum_count"] > 0 else None
            
        result.append(MonthlyGraphData(
            period_value=monday,
            label=f"{idx+1}주",
            avg_rating=avg
        ))
    
    return result
 
@router.get("/foods", response_model=FoodRatingList, summary="음식별 평균 평점 조회", description="각 음식별로 해당 음식이 포함된 식단들의 평균 평점을 조회합니다. 데이터는 1시간마다 업데이트됩니다.")
def get_food_ratings():
    from app.tasks.food_stats import get_cached_food_ratings
    return get_cached_food_ratings()

@router.get("/{stat_id}", response_model=StatisticResponse, summary="통계 상세 조회", description="특정 통계 데이터의 상세 내용 및 AI 코멘트를 조회합니다.")
def get_statistic_detail(stat_id: int, db: Session = Depends(get_db)):
    stat = db.query(Statistic).filter(Statistic.stat_id == stat_id).first()
    if not stat:
        raise HTTPException(status_code=404, detail="통계 정보를 찾을 수 없습니다.")
        
    return StatisticResponse(
        stat_id=stat.stat_id,
        period_type=stat.period_type,
        period_value=stat.period_value,
        avg_rating=float(stat.avg_rating) if stat.avg_rating else None,
        ai_comment=parse_ai_comment(stat.ai_comment),
        total_reviews=stat.total_reviews,
        created_at=stat.created_at
    )
