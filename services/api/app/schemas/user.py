from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from app.schemas.review import ReviewResponse

class UserSignup(BaseModel):
    student_id: str = Field(..., description="학번 (ID로 사용, 사전 등록된 정보와 일치해야 함)", example="2401110345")
    name: str = Field(..., description="이름 (사전 등록된 정보와 일치해야 함)", example="홍길동")
    phone_number: str = Field(..., description="전화번호 (하이픈 유무 무관, 사전 등록된 정보와 일치해야 함)", example="010-1234-5678")
    password: str = Field(..., description="비밀번호", example="password123")
    birth_date: date = Field(..., description="생년월일 (사전 등록된 정보와 일치해야 함)", example="2005-01-01")
    gender: str = Field(..., description="성별 (F/M, 사전 등록된 정보와 일치해야 함)", pattern="^(F|M)$", example="M")

class Token(BaseModel):
    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field(..., description="토큰 타입", example="bearer")

class UserInfo(BaseModel):
    student_id: str = Field(..., example="2401110345")
    name: str = Field(..., example="홍길동")
    phone_number: Optional[str] = Field(None, example="010-1234-5678")
    birth_date: Optional[date] = Field(None, example="2005-01-01")
    gender: Optional[str] = Field(None, example="M")

    class Config:
        from_attributes = True
