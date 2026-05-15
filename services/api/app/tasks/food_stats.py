from sqlalchemy import text
from app.db.session import engine
from datetime import datetime
import logging

logger = logging.getLogger("food_stats")

# 글로벌 변수에 캐싱
cached_food_ratings = {
    "foods": [],
    "updated_at": None
}

def update_food_ratings():
    """
    베이지안 평균(Bayesian Average)을 사용하여 음식별 신뢰 평점을 계산합니다.
    평가 인원이 적은 경우 전체 평균에 가깝게 보정됩니다.
    """
    logger.info("음식별 신뢰 평점 계산 작업 시작 (Bayesian Average 적용)")
    try:
        with engine.connect() as conn:
            # 1. 시스템 전체 평균 평점(C) 계산
            c_res = conn.execute(text("SELECT AVG(rating) FROM reviews")).fetchone()
            system_avg = float(c_res[0]) if c_res[0] is not None else 3.0
            
            # 2. 최소 신뢰 리뷰 수(m) 설정: 5건으로 가정
            m = 5.0
            
            # 3. 음식별 데이터 집계 및 빈도 필터링 (전체 식단의 20% 이상 등장하는 메뉴 제외)
            query = text("""
                WITH food_appearance AS (
                    SELECT food_id, COUNT(meal_id) as appearance_count
                    FROM meal_foods
                    GROUP BY food_id
                )
                SELECT 
                    f.food_id,
                    f.name, 
                    SUM(m.avg_rating * m.review_count) as sum_weighted_rating,
                    SUM(m.review_count) as total_reviews,
                    COUNT(m.meal_id) as meal_count,
                    fa.appearance_count
                FROM foods f
                JOIN meal_foods mf ON f.food_id = mf.food_id
                JOIN meals m ON mf.meal_id = m.meal_id
                JOIN food_appearance fa ON f.food_id = fa.food_id
                WHERE m.review_count > 0
                GROUP BY f.food_id, f.name, fa.appearance_count
                HAVING fa.appearance_count < (SELECT COUNT(*) FROM meals) * 0.3
            """)
            result = conn.execute(query).fetchall()
            
            foods = []
            for row in result:
                v = float(row.total_reviews) # 해당 음식에 달린 총 리뷰 수
                R = float(row.sum_weighted_rating) / v # 해당 음식의 단순 평균 평점
                
                # 베이지안 평균 공식 적용: (v / (v + m)) * R + (m / (v + m)) * C
                weighted_rating = (v / (v + m)) * R + (m / (v + m)) * system_avg
                
                foods.append({
                    "food_id": row.food_id,
                    "name": row.name,
                    "avg_rating": round(weighted_rating, 1),
                    "meal_count": row.meal_count
                })
            
            # 평점 내림차순 정렬
            foods.sort(key=lambda x: x["avg_rating"], reverse=True)
            
            global cached_food_ratings
            cached_food_ratings["foods"] = foods
            cached_food_ratings["updated_at"] = datetime.now()
            logger.info(f"음식별 신뢰 평점 계산 완료 (시스템 평균: {system_avg:.2f}, 대상: {len(foods)}건)")
            
    except Exception as e:
        logger.error(f"음식별 평점 계산 중 오류 발생: {str(e)}")

def get_cached_food_ratings():
    """
    캐싱된 음식 평점 데이터를 반환합니다.
    """
    return cached_food_ratings
