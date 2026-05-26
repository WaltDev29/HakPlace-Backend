-- 1. 2026-05-25 이후의 식단 데이터 삭제 
-- (외래 키의 ON DELETE CASCADE 설정으로 인해 meal_foods 테이블의 관련 데이터도 자동 삭제됨)
DELETE FROM meals 
WHERE served_date >= '2026-05-25';
-- 2. 고아(Orphan) 데이터 정리: 어떤 식단(meal_foods)에도 포함되어 있지 않은 음식(foods) 삭제
-- (만약 위 1번 삭제로 인해 더 이상 쓰이지 않게 된 음식 이름이 있다면 정리)
DELETE FROM foods 
WHERE food_id NOT IN (
    SELECT DISTINCT food_id FROM meal_foods
);