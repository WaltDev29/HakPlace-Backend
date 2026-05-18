import json
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import text

# 프로젝트 루트를 PYTHONPATH에 추가하여 패키지 임포트 지원
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# .env.api 파일에서 환경 변수 로드 (Docker 설정 및 DB 접속용)
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../docker/env/.env.api"))
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value.strip()

# 로컬(개발환경) 테스트 시 db 호스트를 localhost로 자동 매핑
if not os.path.exists('/.dockerenv'):
    db_url = os.getenv("DATABASE_URL")
    if db_url and "@db:" in db_url:
        os.environ["DATABASE_URL"] = db_url.replace("@db:", "@localhost:")

from app.db.session import engine
from app.services.ai_analysis import ai_service
from app.utils.date_utils import get_monday_date

def force_run_weekly(monday_str: str):
    print("\n" + "="*60)
    print(f" 🚀 [FORCE RUN] 주간 AI 분석 및 DB 저장 강제 실행 ({monday_str})")
    print("="*60)
    
    try:
        monday_dt = datetime.strptime(monday_str, "%Y-%m-%d")
        sunday_dt = monday_dt + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        with engine.begin() as conn:
            # 1. 이번 주 식단 및 리뷰 데이터 가져오기
            print("ℹ️ 1. 주간 식단 및 리뷰 데이터 조회 중...")
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
            print(f" -> 조회된 식단 수: {len(meals_data)}개")
            print(f" -> 주간 평균 평점: {current_avg_rating}")
            print(f" -> 주간 총 리뷰 건수: {total_reviews_count}")

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
                    print(f"⚠️ 이전 분석 결과 파싱 중 예외: {e}")

            # meals_data에 이전 평점 주입
            for m in meals_data:
                key = (m["date"], m["type"])
                m["prev_rating"] = prev_ratings_map.get(key, 0.0)

            # 3. AI 분석 호출 (Gemini 모델 활용)
            print("\n🤖 2. AI 분석 호출 중 (Gemini API)...")
            context = {
                "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "period_value": monday_str,
                "meals": meals_data
            }
            ai_result = ai_service.analyze_weekly_reviews(context, previous_analysis_json)
            print(" -> AI 리뷰 분석 완료!")

            # 주간 베스트 식단 조회 및 포맷팅 (박제 방식)
            print("ℹ️ 2.1. 주간 베스트 식단 계산 중...")
            try:
                best_meal_query = text("""
                    SELECT m.served_date, m.meal_type, m.avg_rating, GROUP_CONCAT(f.name SEPARATOR ', ') as foods
                    FROM meals m
                    LEFT JOIN meal_foods mf ON m.meal_id = mf.meal_id
                    LEFT JOIN foods f ON mf.food_id = f.food_id
                    WHERE m.served_date BETWEEN :start AND :end AND m.avg_rating > 0
                    GROUP BY m.meal_id
                    ORDER BY m.avg_rating DESC, m.review_count DESC
                    LIMIT 1
                """)
                best_row = conn.execute(best_meal_query, {"start": monday_dt.date(), "end": sunday_dt.date()}).fetchone()
                best_meal_str = None
                if best_row and best_row.avg_rating:
                    days = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
                    day_name = days[best_row.served_date.weekday()]
                    date_str = best_row.served_date.strftime("%Y-%m-%d")
                    avg_rating = f"{float(best_row.avg_rating):.1f}"
                    foods_str = f"{best_row.foods}" if best_row.foods else ""
                    best_meal_str = f"{date_str} {day_name}\n평점 : {avg_rating}\n 식단 : {foods_str}"
                    print(f" -> 주간 베스트 식단 도출:\n{best_meal_str}")
                else:
                    print(" -> 베스트 식단 조건에 부합하는 데이터가 없습니다.")
                
                if isinstance(ai_result, dict):
                    ai_result["best_meal"] = best_meal_str
            except Exception as e:
                print(f"❌ 주간 베스트 식단 도출 실패: {e}")

            # 4. DB 저장 (Upsert)
            print("\n💾 3. DB에 주간 통계 저장 (Upsert)...")
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
            print(f"✨ 성공: {monday_str} 주간 AI 분석 결과가 DB에 성공적으로 저장되었습니다.")
            print("="*60 + "\n")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # 파라미터가 입력되면 특정 주(YYYY-MM-DD, 해당 주의 월요일)에 대해 실행하고, 없으면 이번 주 월요일 기준 실행
    if len(sys.argv) > 1:
        target_monday = sys.argv[1]
        try:
            datetime.strptime(target_monday, "%Y-%m-%d")
        except ValueError:
            print("❌ 오류: 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 포맷(해당 주의 월요일)으로 입력해주세요. (예: 2026-05-11)")
            sys.exit(1)
    else:
        target_monday = get_monday_date(datetime.now())
        
    force_run_weekly(target_monday)
