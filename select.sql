SELECT 
    m.served_date AS '날짜',
    CASE DAYOFWEEK(m.served_date)
        WHEN 2 THEN '월요일'
        WHEN 3 THEN '화요일'
        WHEN 4 THEN '수요일'
        WHEN 5 THEN '목요일'
        WHEN 6 THEN '금요일'
    END AS '요일',
    m.meal_type AS '식단 종류',
    GROUP_CONCAT(f.name ORDER BY f.food_id ASC SEPARATOR ', ') AS '메뉴'
FROM 
    meals m
LEFT JOIN 
    meal_foods mf ON m.meal_id = mf.meal_id
LEFT JOIN 
    foods f ON mf.food_id = f.food_id
WHERE 
    DAYOFWEEK(m.served_date) BETWEEN 2 AND 6 -- 월(2) ~ 금(6) 요일 필터링 (주말 제외)
    
    -- 특정 주차의 데이터만 보고 싶으시다면 아래 주석을 해제하고 날짜 범위를 입력하세요.
    -- AND m.served_date BETWEEN '2024-05-20' AND '2024-05-24'
GROUP BY 
    m.meal_id, m.served_date, m.meal_type
ORDER BY 
    m.served_date ASC, 
    FIELD(m.meal_type, '조식', '중식', '석식'); -- 조/중/석식 순서대로 정렬
