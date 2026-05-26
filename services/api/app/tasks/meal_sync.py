from playwright.sync_api import sync_playwright
from sqlalchemy import text
from app.db.session import engine
import logging

# 로깅 설정
logger = logging.getLogger("meal_sync")

def clean_food_name(name):
    """음식 이름 정제: 공백 제거 및 특수 기호 기준 분리"""
    name = name.replace(' ', '').strip()
    for sep in [',']:
        name = name.replace(sep, '|')
    return [n for n in name.split('|') if n]

def log_summary(stats):
    """최종 실행 결과를 로그로 출력"""
    summary = []
    summary.append("\n" + "="*50)
    summary.append("           학식 데이터 동기화 결과 리포트")
    summary.append("="*50)
    
    dates_str = ', '.join(sorted(list(stats['dates']))) if stats['dates'] else "없음"
    summary.append(f"📅 크롤링 날짜: {dates_str}")
    summary.append("-" * 50)
    
    summary.append(f"🍱 식단 세션 (Meals)")
    summary.append(f"   - 총 시도: {stats['total_meals']}건")
    summary.append(f"   - 신규 등록: {stats['new_meals']}건")
    summary.append(f"   - 기존 항목: {stats['existing_meals']}건")
    
    summary.append(f"\n🍎 개별 음식 (Foods)")
    summary.append(f"   - 총 발견: {stats['total_foods']}건")
    summary.append(f"   - 신규 등록: {stats['new_foods']}건")
    summary.append(f"   - 기존 항목: {stats['existing_foods']}건")
    
    if stats["errors"]:
        summary.append("-" * 50)
        summary.append("❌ 발생한 에러:")
        for err in stats["errors"]:
            summary.append(f"   - {err}")
    
    summary.append("=" * 50)
    if not stats["errors"]:
        summary.append("[✔] 모든 작업이 성공적으로 완료되었습니다.")
    summary.append("=" * 50)
    
    # 리스트에 담긴 모든 줄을 로그로 출력
    logger.info("\n".join(summary))

def crawl_and_sync():
    logger.info("학식 데이터 동기화 태스크 시작")
    
    # 통계 데이터 초기화
    stats = {
        "dates": set(),
        "total_meals": 0,
        "new_meals": 0,
        "existing_meals": 0,
        "total_foods": 0,
        "new_foods": 0,
        "existing_foods": 0,
        "errors": []
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("https://www.kopo.ac.kr/jungsu/content.do?menu=247", timeout=60000)
            
            # 행(row) 단위로 가져오기 (월~금 5일)
            trs = page.query_selector_all(".menu tbody tr")[:5]
            meal_data = []
            
            for tr in trs:
                tds = tr.query_selector_all("td")
                if not tds:
                    continue
                
                # 첫 번째 셀(td)은 날짜
                date_text = tds[0].inner_text().split()[0]
                stats["dates"].add(date_text)
                
                # 나머지 셀(td)은 각각 조식, 중식, 석식
                for col_idx in range(1, 4):
                    if col_idx < len(tds):
                        menu_raw = tds[col_idx].inner_text().replace('\r', '').replace('\n', ',')
                    else:
                        menu_raw = ""
                        
                    meal_data.append({
                        "date": date_text,
                        "type": ['조식', '중식', '석식'][col_idx - 1],
                        "menu_raw": menu_raw
                    })
            browser.close()
    except Exception as e:
        stats["errors"].append(f"크롤링 에러: {str(e)}")
        log_summary(stats)
        return

    try:
        with engine.begin() as conn:
            for item in meal_data:
                stats["total_meals"] += 1
                # Meals 저장
                res_meal = conn.execute(
                    text("INSERT IGNORE INTO meals (served_date, meal_type) VALUES (:d, :t)"),
                    {"d": item['date'], "t": item['type']}
                )
                
                if res_meal.rowcount > 0:
                    stats["new_meals"] += 1
                else:
                    stats["existing_meals"] += 1
                
                meal_res = conn.execute(
                    text("SELECT meal_id FROM meals WHERE served_date = :d AND meal_type = :t"),
                    {"d": item['date'], "t": item['type']}
                ).fetchone()
                meal_id = meal_res[0]

                # Foods 처리
                raw_menu = item['menu_raw']
                if not raw_menu or raw_menu == 'nan':
                    continue

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
                    else:
                        stats["existing_foods"] += 1
                    
                    food_id_res = conn.execute(
                        text("SELECT food_id FROM foods WHERE name = :n"),
                        {"n": food_name}
                    ).fetchone()
                    food_id = food_id_res[0]
                    
                    conn.execute(
                        text("INSERT IGNORE INTO meal_foods (meal_id, food_id) VALUES (:mid, :fid)"),
                        {"mid": meal_id, "fid": food_id}
                    )
    except Exception as e:
        stats["errors"].append(f"DB 동기화 에러: {str(e)}")

    # 최종 리포트 출력
    log_summary(stats)
