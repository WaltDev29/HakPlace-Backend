from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class StatisticResponse(BaseModel):
    stat_id: int = Field(..., example=1)
    period_type: str = Field(..., description="기간 타입 (WEEKLY/MONTHLY)", example="WEEKLY")
    period_value: str = Field(..., description="기간 값", example="2024-05-W1")
    avg_rating: Optional[float] = Field(None, example=4.2)
    ai_comment: Optional[str] = Field(None, example="이번 주 제육볶음이 특히 인기가 많았습니다.")
    total_reviews: int = Field(..., example=45)
    created_at: datetime

    class Config:
        from_attributes = True

class StatisticList(BaseModel):
    stats: List[StatisticResponse]
