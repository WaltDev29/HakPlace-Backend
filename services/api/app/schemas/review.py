from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ReviewCreate(BaseModel):
    meal_id: int = Field(..., description="식단 ID", example=101)
    rating: float = Field(..., description="평점 (1.0~5.0)", ge=1.0, le=5.0, example=5.0)
    review_comment: Optional[str] = Field(None, description="리뷰 내용", example="정말 맛있어요!")
    photo_base64: Optional[str] = Field(None, description="이미지 (Base64)", example="data:image/png;base64,...")

class ReviewResponse(BaseModel):
    review_id: int = Field(..., example=1)
    student_name: str = Field(..., example="홍길동")
    meal_id: int = Field(..., example=101)
    rating: float = Field(..., example=5.0)
    review_comment: Optional[str] = Field(None, example="정말 맛있어요!")
    photo_url: Optional[str] = Field(None, example="/static/uploads/uuid.png")
    created_at: datetime

    class Config:
        from_attributes = True

class ReviewList(BaseModel):
    reviews: List[ReviewResponse]
    total: int = Field(..., example=1)
