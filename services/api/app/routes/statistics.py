from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Statistic
from app.schemas.statistic import StatisticResponse, StatisticList, FoodRatingList
from typing import Optional

router = APIRouter()

@router.get("/", response_model=StatisticList, summary="전체 통계 목록 조회", description="주차별 또는 월별로 생성된 모든 AI 분석 통계 데이터를 조회합니다.")
def get_statistics(
    period_type: Optional[str] = None, # WEEKLY, MONTHLY
    db: Session = Depends(get_db)
):
    query = db.query(Statistic)
    if period_type:
        query = query.filter(Statistic.period_type == period_type)
        
    stats = query.order_by(Statistic.period_value.desc()).all()
    
    # Decimal 객체를 float으로 변환하여 반환 (Pydantic 처리용)
    res = []
    for s in stats:
        res.append(StatisticResponse(
            stat_id=s.stat_id,
            period_type=s.period_type,
            period_value=s.period_value,
            avg_rating=float(s.avg_rating) if s.avg_rating else None,
            ai_comment=s.ai_comment,
            total_reviews=s.total_reviews,
            created_at=s.created_at
        ))
        
    return StatisticList(stats=res)
 
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
        ai_comment=stat.ai_comment,
        total_reviews=stat.total_reviews,
        created_at=stat.created_at
    )
