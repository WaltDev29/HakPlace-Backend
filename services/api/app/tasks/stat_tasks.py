import json
import logging
from datetime import datetime, timedelta
from sqlalchemy import text
from app.db.session import engine
from app.utils.date_utils import get_monday_date, is_last_saturday, get_month_str
from app.services.ai_analysis import ai_service

logger = logging.getLogger("stat_tasks")

def update_weekly_stats():
    """
    주간 리뷰 분석 및 통계 업데이트 (평일 오전 8시 & 토요일)
    - 이번 주 월요일부터 현재까지의 데이터를 분석합니다.
    - 기존에 생성된 레코드가 있다면 해당 JSON 내용을 AI에게 함께 전달하여 변화를 분석하게 합니다.
    """
    now = datetime.now()
    monday_str = get_monday_date(now)
    monday_dt = datetime.strptime(monday_str, "%Y-%m-%d")
    # 주의 끝(일요일 23:59:59) 계산
    sunday_dt = monday_dt + timedelta(days=6, hours=23, minutes=59, seconds=59)

    logger.info(f"주간 통계 업데이트 시작: {monday_str}")

    try:
        with engine.begin() as conn:
            # 1. 이번 주 식단 및 리뷰 데이터 가져오기
            query = text("""
                SELECT 
                    m.meal_id, m.served_date, m.meal_type, m.avg_rating,
                    GROUP_CONCAT(f.name SEPARATOR ', ') as foods
                FROM meals m
                LEFT JOIN meal_foods mf ON m.meal_id = mf.meal_id
                LEFT JOIN foods f ON mf.food_id = f.food_id
                WHERE m.served_date BETWEEN :start AND :end
                GROUP BY m.meal_id
                ORDER BY m.served_date ASC, m.meal_type ASC
            """)
            meals_res = conn.execute(query, {"start": monday_dt.date(), "end": sunday_dt.date()}).fetchall()

            meals_data = []
            total_rating_sum = 0
            meals_with_rating = 0
            total_reviews_count = 0

            for row in meals_res:
                # 해당 식단의 리뷰 텍스트 가져오기
                rev_query = text("SELECT review_comment FROM reviews WHERE meal_id = :mid AND review_comment IS NOT NULL")
                reviews = conn.execute(rev_query, {"mid": row.meal_id}).fetchall()
                
                # 식단별 총 리뷰 수 합산
                cnt_query = text("SELECT COUNT(*) FROM reviews WHERE meal_id = :mid")
                count = conn.execute(cnt_query, {"mid": row.meal_id}).fetchone()[0]
                total_reviews_count += count

                meals_data.append({
                    "date": str(row.served_date),
                    "day": row.served_date.strftime("%a"),
                    "type": row.meal_type,
                    "avg_rating": float(row.avg_rating) if row.avg_rating else 0.0,
                    "foods": row.foods.split(', ') if row.foods else [],
                    "reviews": [r[0] for r in reviews if r[0].strip()]
                })
                
                if row.avg_rating and row.avg_rating > 0:
                    total_rating_sum += float(row.avg_rating)
                    meals_with_rating += 1

            current_avg_rating = round(total_rating_sum / meals_with_rating, 2) if meals_with_rating > 0 else 0.0

            # 2. 기존 분석 결과(JSON) 가져오기 (비교 분석용)
            prev_query = text("SELECT ai_comment FROM statistics WHERE period_type = 'WEEKLY' AND period_value = :val")
            prev_res = conn.execute(prev_query, {"val": monday_str}).fetchone()
            previous_analysis_json = prev_res[0] if prev_res else None

            # 이전 평점 데이터 맵 생성 (date, type) -> avg_rating
            prev_ratings_map = {}
            if previous_analysis_json:
                try:
                    prev_data = json.loads(previous_analysis_json)
                    for m in prev_data.get("meals_summary", []):
                        key = (m.get("date"), m.get("type"))
                        prev_ratings_map[key] = m.get("avg_rating")
                except Exception as e:
                    logger.warning(f"이전 분석 결과 파싱 중 오류 발생: {e}")

            # 3. meals_data에 이전 평점 주입
            for m in meals_data:
                key = (m["date"], m["type"])
                m["prev_rating"] = prev_ratings_map.get(key, 0.0)

            # 4. AI 분석 호출
            context = {
                "analysis_date": now.strftime("%Y-%m-%d %H:%M"),
                "period_value": monday_str,
                "meals": meals_data
            }
            ai_result = ai_service.analyze_weekly_reviews(context, previous_analysis_json)

            # 5. DB 저장 (Upsert)
            upsert_query = text("""
                INSERT INTO statistics (period_type, period_value, avg_rating, ai_comment, total_reviews)
                VALUES ('WEEKLY', :val, :avg, :ai, :total)
                ON DUPLICATE KEY UPDATE
                    avg_rating = VALUES(avg_rating),
                    ai_comment = VALUES(ai_comment),
                    total_reviews = VALUES(total_reviews),
                    created_at = CURRENT_TIMESTAMP
            """)
            conn.execute(upsert_query, {
                "val": monday_str,
                "avg": current_avg_rating,
                "ai": json.dumps(ai_result, ensure_ascii=False),
                "total": total_reviews_count
            })

            logger.info(f"주간 통계 업데이트 완료: {monday_str} (평점: {current_avg_rating}, 리뷰: {total_reviews_count})")

    except Exception as e:
        logger.error(f"주간 통계 업데이트 중 오류 발생: {str(e)}")

def update_monthly_stats():
    """
    월간 리뷰 분석 및 통계 업데이트 (매달 마지막 토요일 실행)
    - 이번 달의 주간 통계들을 모아 종합적인 분석을 수행합니다.
    """
    now = datetime.now()
    
    # 마지막 주 토요일인지 체크
    if not is_last_saturday(now):
        logger.info("오늘은 마지막 주 토요일이 아닙니다. 월간 분석을 건너뜁니다.")
        return

    month_str = get_month_str(now)
    logger.info(f"월간 통계 업데이트 시작: {month_str}")

    try:
        with engine.begin() as conn:
            # 1. 이번 달의 주간 통계 데이터 가져오기
            query = text("""
                SELECT period_value, avg_rating, ai_comment, total_reviews
                FROM statistics
                WHERE period_type = 'WEEKLY' AND period_value LIKE :pattern
                ORDER BY period_value ASC
            """)
            weekly_res = conn.execute(query, {"pattern": f"{month_str}%"}).fetchall()

            if not weekly_res:
                logger.warning(f"{month_str}에 대한 주간 데이터가 존재하지 않아 월간 분석을 수행할 수 없습니다.")
                return

            weekly_summaries = []
            total_rating_sum = 0
            total_reviews_sum = 0
            
            for row in weekly_res:
                try:
                    ai_data = json.loads(row.ai_comment) if row.ai_comment else {}
                except:
                    ai_data = {"ai_analysis": row.ai_comment} # 폴백
                
                weekly_summaries.append({
                    "period_value": row.period_value,
                    "avg_rating": float(row.avg_rating),
                    "ai_analysis": ai_data.get("ai_analysis", ""),
                    "total_reviews": row.total_reviews
                })
                total_rating_sum += float(row.avg_rating)
                total_reviews_sum += row.total_reviews

            monthly_avg_rating = round(total_rating_sum / len(weekly_res), 2)

            # 2. AI 분석 호출
            context = {
                "analysis_date": now.strftime("%Y-%m-%d"),
                "period_value": month_str,
                "weekly_summaries": weekly_summaries
            }
            ai_result = ai_service.analyze_monthly_reviews(context)

            # 3. DB 저장 (Upsert)
            upsert_query = text("""
                INSERT INTO statistics (period_type, period_value, avg_rating, ai_comment, total_reviews)
                VALUES ('MONTHLY', :val, :avg, :ai, :total)
                ON DUPLICATE KEY UPDATE
                    avg_rating = VALUES(avg_rating),
                    ai_comment = VALUES(ai_comment),
                    total_reviews = VALUES(total_reviews),
                    created_at = CURRENT_TIMESTAMP
            """)
            conn.execute(upsert_query, {
                "val": month_str,
                "avg": monthly_avg_rating,
                "ai": json.dumps(ai_result, ensure_ascii=False),
                "total": total_reviews_sum
            })

            logger.info(f"월간 통계 업데이트 완료: {month_str} (평점: {monthly_avg_rating})")

    except Exception as e:
        logger.error(f"월간 통계 업데이트 중 오류 발생: {str(e)}")

def run_saturday_stats():
    """토요일 오전 8시 최종 주간 분석 및 월간 분석 통합 실행"""
    update_weekly_stats()
    update_monthly_stats()
