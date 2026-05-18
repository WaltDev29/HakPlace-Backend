import json
import os
import sys
from datetime import datetime
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

def force_run_monthly(month_str: str):
    print("\n" + "="*60)
    print(f" 🚀 [FORCE RUN] 월간 AI 분석 및 DB 저장 강제 실행 ({month_str})")
    print("="*60)
    
    try:
        with engine.begin() as conn:
            # 1. 해당 월의 주간 통계 데이터 가져오기
            print("ℹ️ 1. 주간 통계 데이터 조회 중...")
            query = text("""
                SELECT period_value, avg_rating, ai_comment, total_reviews
                FROM statistics
                WHERE period_type = 'WEEKLY' AND period_value LIKE :pattern
                ORDER BY period_value ASC
            """)
            weekly_res = conn.execute(query, {"pattern": f"{month_str}%"}).fetchall()

            if not weekly_res:
                print(f"❌ 오류: {month_str}에 대한 주간 분석 데이터(WEEKLY)가 DB에 존재하지 않아 월간 통합 분석을 수행할 수 없습니다.")
                sys.exit(1)

            weekly_summaries = []
            total_rating_sum = 0
            total_reviews_sum = 0
            
            for row in weekly_res:
                try:
                    ai_data = json.loads(row.ai_comment) if row.ai_comment else {}
                except Exception:
                    ai_data = {"ai_analysis": row.ai_comment}
                
                weekly_summaries.append({
                    "period_value": row.period_value,
                    "avg_rating": float(row.avg_rating),
                    "ai_analysis": ai_data.get("ai_analysis", ""),
                    "total_reviews": row.total_reviews
                })
                total_rating_sum += float(row.avg_rating)
                total_reviews_sum += row.total_reviews

            monthly_avg_rating = round(total_rating_sum / len(weekly_res), 2)
            print(f" -> 수집된 주차(WEEKLY) 수: {len(weekly_summaries)}개")
            print(f" -> 월간 가중 평균 평점: {monthly_avg_rating}")
            print(f" -> 월간 총 리뷰 건수: {total_reviews_sum}")

            # 2. AI 분석 호출 (Gemini 모델 활용)
            print("\n🤖 2. AI 분석 호출 중 (Gemini API)...")
            context = {
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "period_value": month_str,
                "weekly_summaries": weekly_summaries
            }
            ai_result = ai_service.analyze_monthly_reviews(context)
            print(" -> AI 리뷰 분석 완료!")

            # 월간 베스트 식단 조회 및 포맷팅 (박제 방식)
            import calendar
            print("ℹ️ 2.1. 월간 베스트 식단 계산 중...")
            try:
                year, month = map(int, month_str.split("-"))
                num_days = calendar.monthrange(year, month)[1]
                start_date = datetime(year, month, 1).date()
                end_date = datetime(year, month, num_days).date()
                
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
                best_row = conn.execute(best_meal_query, {"start": start_date, "end": end_date}).fetchone()
                best_meal_str = None
                if best_row and best_row.avg_rating:
                    days = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
                    day_name = days[best_row.served_date.weekday()]
                    date_str = best_row.served_date.strftime("%Y-%m-%d")
                    avg_rating = f"{float(best_row.avg_rating):.1f}"
                    foods_str = f"{best_row.foods}" if best_row.foods else ""
                    best_meal_str = f"{date_str} {day_name}\n평점 : {avg_rating}\n식단 : {foods_str}"
                    print(f" -> 월간 베스트 식단 도출:\n{best_meal_str}")
                else:
                    print(" -> 베스트 식단 조건에 부합하는 데이터가 없습니다.")
                
                if isinstance(ai_result, dict):
                    ai_result["best_meal"] = best_meal_str
            except Exception as e:
                print(f"❌ 월간 베스트 식단 도출 실패: {e}")

            # 3. DB 저장 (Upsert)
            print("\n💾 3. DB에 월간 통계 저장 (Upsert)...")
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
            print(f"✨ 성공: {month_str} 월간 통합 AI 분석 결과가 DB에 성공적으로 저장되었습니다.")
            print("="*60 + "\n")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # 파라미터가 입력되면 특정 월(YYYY-MM)에 대해 실행하고, 없으면 현재 월 기준 실행
    if len(sys.argv) > 1:
        target_month = sys.argv[1]
        try:
            datetime.strptime(target_month, "%Y-%m")
        except ValueError:
            print("❌ 오류: 날짜 형식이 올바르지 않습니다. YYYY-MM 포맷으로 입력해주세요. (예: 2026-05)")
            sys.exit(1)
    else:
        target_month = datetime.now().strftime("%Y-%m")
        
    force_run_monthly(target_month)
