from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class MealSummaryItem(BaseModel):
    date: str = Field(..., example="2026-05-11")
    day: str = Field(..., example="월")
    type: str = Field(..., example="중식")
    avg_rating: float = Field(..., example=4.5)
    prev_rating: float = Field(..., description="이전 분석 시점의 평점", example=4.0)
    foods: List[str] = Field(..., example=["제육볶음", "상추쌈"])

class WeeklyAIComment(BaseModel):
    analysis_date: str = Field(..., description="분석 실행 시간", example="2026-05-14 10:00")
    period_value: str = Field(..., description="분석 대상 주 (월요일 날짜)", example="2026-05-11")
    meals_summary: List[MealSummaryItem] = Field(..., description="해당 주차 식단 요약")
    ai_analysis: str = Field(..., description="AI 총평", example="이번 주는 전반적으로 평점이 상승세입니다.")
    trend_analysis: str = Field(..., description="평가 변화 추이 분석", example="지난 업데이트 대비 만족도가 상승했습니다.")
    best_meal: str = Field(..., description="이번 주 베스트 식단", example="월요일 중식 (제육볶음)")
    improvement_points: str = Field(..., description="개선 필요 사항", example="금요일 석식의 간이 세다는 의견이 있었습니다.")

class MonthlyAIComment(BaseModel):
    analysis_date: str = Field(..., description="분석 실행 날짜", example="2026-05-31")
    period_value: str = Field(..., description="해당 월", example="2026-05")
    ai_analysis: str = Field(..., description="월간 총평")
    monthly_trend: str = Field(..., description="월간 변화 추이")
    top_rated_weeks: List[str] = Field(..., description="우수 주차 목록")
    key_feedback: str = Field(..., description="주요 피드백 요약")

class StatisticResponse(BaseModel):
    stat_id: int = Field(..., example=1)
    period_type: str = Field(..., description="기간 타입 (WEEKLY/MONTHLY)", example="WEEKLY")
    period_value: str = Field(..., description="기간 값 (WEEKLY: 월요일 날짜, MONTHLY: YYYY-MM)", example="2026-05-11")
    avg_rating: Optional[float] = Field(None, example=4.2)
    ai_comment: Union[WeeklyAIComment, MonthlyAIComment, Dict[str, Any], str, None] = Field(
        None, 
        description="구조화된 AI 분석 코멘트 (JSON)",
    )
    total_reviews: int = Field(..., example=45)
    created_at: datetime

    class Config:
        from_attributes = True

class FoodRatingResponse(BaseModel):
    food_id: int = Field(..., example=1)
    name: str = Field(..., example="치킨너겟")
    avg_rating: float = Field(..., example=4.5)
    meal_count: int = Field(..., description="이 음식이 포함된 총 식단 수", example=10)

class FoodRatingList(BaseModel):
    foods: List[FoodRatingResponse]
    updated_at: Optional[datetime] = Field(None, description="마지막 업데이트 시간")

class StatisticList(BaseModel):
    stats: List[StatisticResponse]

class WeeklyGraphData(BaseModel):
    date: str = Field(..., description="날짜", example="2026-05-11")
    label: str = Field(..., description="요일 라벨 (월~금)", example="월")
    avg_rating: Optional[float] = Field(None, description="평균 평점 (없으면 null)", example=4.2)

class MonthlyGraphData(BaseModel):
    period_value: str = Field(..., description="주차 시작일 (월요일 날짜)", example="2026-05-11")
    label: str = Field(..., description="주차 라벨 (1주~5주)", example="1주")
    avg_rating: Optional[float] = Field(None, description="평균 평점 (없으면 null)", example=4.2)
