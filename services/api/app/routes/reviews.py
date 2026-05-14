from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models import Review, Meal, Student
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewList
from app.api.deps import get_current_user
from app.utils.image_utils import save_base64_image
from typing import List, Optional

router = APIRouter()

def update_meal_rating(meal_id: int, db: Session):
    """
    해당 식단의 평균 평점과 리뷰 수를 업데이트합니다.
    """
    stats = db.query(
        func.avg(Review.rating).label('avg_rating'),
        func.count(Review.review_id).label('review_count')
    ).filter(Review.meal_id == meal_id).first()
    
    meal = db.query(Meal).filter(Meal.meal_id == meal_id).first()
    if meal:
        meal.avg_rating = stats.avg_rating or 0.00
        meal.review_count = stats.review_count or 0
        db.add(meal)

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED, summary="리뷰 작성", description="특정 식단에 대한 리뷰를 작성합니다. 이미지(Base64) 첨부가 가능하며, 작성 시 해당 식단의 평균 평점이 자동 갱신됩니다.")
def create_review(
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user)
):
    # 식단 존재 여부 확인
    meal = db.query(Meal).filter(Meal.meal_id == review_in.meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="식단 정보를 찾을 수 없습니다.")
    
    # 이미 작성한 리뷰가 있는지 확인 (UNIQUE 제약 조건 대응)
    existing_review = db.query(Review).filter(
        Review.meal_id == review_in.meal_id,
        Review.student_id == current_user.student_id
    ).first()
    if existing_review:
        raise HTTPException(status_code=400, detail="이미 이 식단에 리뷰를 작성하셨습니다.")

    # 이미지 저장
    photo_url = None
    if review_in.photo_base64:
        photo_url = save_base64_image(review_in.photo_base64)

    # 리뷰 생성
    new_review = Review(
        meal_id=review_in.meal_id,
        student_id=current_user.student_id,
        rating=review_in.rating,
        review_comment=review_in.review_comment,
        photo_url=photo_url
    )
    db.add(new_review)
    
    # 평점 업데이트 및 커밋
    try:
        db.commit()
        db.refresh(new_review)
        update_meal_rating(new_review.meal_id, db)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"리뷰 저장 중 오류 발생: {str(e)}")

    # 반환 데이터 구성 (학생 이름 포함)
    return ReviewResponse(
        review_id=new_review.review_id,
        student_name=current_user.name,
        meal_id=new_review.meal_id,
        rating=new_review.rating,
        review_comment=new_review.review_comment,
        photo_url=new_review.photo_url,
        created_at=new_review.created_at
    )

@router.get("/", response_model=ReviewList, summary="리뷰 목록 조회", description="식단 ID 또는 학생 ID별로 리뷰를 필터링하여 조회합니다. 최신순, 평점순 정렬을 지원합니다.")
def list_reviews(
    meal_id: Optional[int] = None,
    student_id: Optional[str] = None,
    sort_by: str = "newest", # newest, highest, lowest
    db: Session = Depends(get_db)
):
    query = db.query(Review).join(Student)
    
    if meal_id:
        query = query.filter(Review.meal_id == meal_id)
    if student_id:
        query = query.filter(Review.student_id == student_id)
        
    if sort_by == "highest":
        query = query.order_by(Review.rating.desc(), Review.created_at.desc())
    elif sort_by == "lowest":
        query = query.order_by(Review.rating.asc(), Review.created_at.desc())
    else: # newest
        query = query.order_by(Review.created_at.desc())
        
    reviews = query.all()
    
    res = []
    for r in reviews:
        res.append(ReviewResponse(
            review_id=r.review_id,
            student_name=r.student.name,
            meal_id=r.meal_id,
            rating=r.rating,
            review_comment=r.review_comment,
            photo_url=r.photo_url,
            created_at=r.created_at
        ))
        
    return ReviewList(reviews=res, total=len(res))
