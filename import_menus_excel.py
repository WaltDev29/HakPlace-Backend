import pandas as pd
from sqlalchemy import text
import logging
import sys
import os

# app 디렉토리를 path에 추가하여 모듈 임포트 가능하게 함
sys.path.append(os.path.join(os.getcwd(), 'services', 'api'))

# DATABASE_URL 환경 변수 설정 (로컬 실행용)
env_path = os.path.join(os.getcwd(), 'docker', 'env', '.env.api')
database_url = None

if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                database_url = line.strip().split('=')[1]
                # docker 내부 호스트 'db'를 'localhost'로 치환
                database_url = database_url.replace('@db:', '@localhost:')
                break

if not database_url:
    print("Error: DATABASE_URL을 .env.api 파일에서 찾을 수 없습니다.")
    sys.exit(1)

# app 패키지를 임포트하지 않고 직접 엔진 생성 (의존성 문제 해결)
from sqlalchemy import create_engine
engine = create_engine(database_url)
print(f"DEBUG: DB 연결 시도 중... ({database_url.split('@')[1]})")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("excel_import")

def clean_food_name(name):
    """음식 이름 정제: 공백 제거 및 특수 기호 기준 분리 (최신 meal_sync 로직 적용)"""
    name = name.replace(' ', '').strip()
    # 현재 meal_sync.py에서는 [','] 만 구분자로 사용함
    for sep in [',']:
        name = name.replace(sep, '|')
    return [n for n in name.split('|') if n]

def import_excel(file_path):
    logger.info(f"Excel 파일 읽기 시작: {file_path}")
    
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        logger.error(f"Excel 파일 읽기 실패: {e}")
        return

    stats = {
        "total_meals": 0,
        "new_meals": 0,
        "total_foods": 0,
        "new_foods": 0
    }

    try:
        with engine.begin() as conn:
            for _, row in df.iterrows():
                date_val = str(row['날짜']).split()[0] # YYYY-MM-DD 형식 추출
                
                for meal_type in ['조식', '중식', '석식']:
                    raw_menu = str(row[meal_type])
                    
                    if not raw_menu or raw_menu == 'nan' or raw_menu.strip() == '':
                        continue

                    stats["total_meals"] += 1
                    
                    # 1. Meals 저장
                    res_meal = conn.execute(
                        text("INSERT IGNORE INTO meals (served_date, meal_type) VALUES (:d, :t)"),
                        {"d": date_val, "t": meal_type}
                    )
                    
                    if res_meal.rowcount > 0:
                        stats["new_meals"] += 1

                    meal_res = conn.execute(
                        text("SELECT meal_id FROM meals WHERE served_date = :d AND meal_type = :t"),
                        {"d": date_val, "t": meal_type}
                    ).fetchone()
                    meal_id = meal_res[0]

                    # 2. Foods 처리
                    # Excel 데이터는 보통 ','로 구분되어 있음
                    foods_list = []
                    for part in raw_menu.split(','):
                        foods_list.extend(clean_food_name(part))

                    for food_name in set(foods_list):
                        stats["total_foods"] += 1
                        
                        # foods 저장
                        res_food = conn.execute(
                            text("INSERT IGNORE INTO foods (name) VALUES (:n)"),
                            {"n": food_name}
                        )
                        
                        if res_food.rowcount > 0:
                            stats["new_foods"] += 1
                        
                        food_id_res = conn.execute(
                            text("SELECT food_id FROM foods WHERE name = :n"),
                            {"n": food_name}
                        ).fetchone()
                        food_id = food_id_res[0]
                        
                        # 3. 매핑 저장
                        conn.execute(
                            text("INSERT IGNORE INTO meal_foods (meal_id, food_id) VALUES (:mid, :fid)"),
                            {"mid": meal_id, "fid": food_id}
                        )
        
        logger.info("="*50)
        logger.info(f"임포트 완료!")
        logger.info(f" - 식단: 총 {stats['total_meals']}건 중 {stats['new_meals']}건 신규 등록")
        logger.info(f" - 음식: 총 {stats['total_foods']}건 중 {stats['new_foods']}건 신규 등록")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"DB 작업 중 에러 발생: {e}")

if __name__ == "__main__":
    import_excel('menus.xlsx')
