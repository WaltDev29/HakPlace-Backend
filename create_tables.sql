-- 1. meals (식단 정보)
CREATE TABLE meals (
    meal_id INT AUTO_INCREMENT PRIMARY KEY,
    served_date DATE NOT NULL,
    meal_type VARCHAR(20) NOT NULL,
    avg_rating DECIMAL(3, 2) DEFAULT 0.00,
    review_count INT DEFAULT 0,
    UNIQUE(served_date, meal_type),
    CONSTRAINT chk_meal_type CHECK (meal_type IN ('조식', '중식', '석식'))
) COMMENT='식사 세션 정보 및 실시간 평점 요약';

-- 2. foods (단일 음식 정보)
CREATE TABLE foods (
    food_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
) COMMENT='음식 개별 항목';

-- 3. meal_foods (식단-음식 매핑)
CREATE TABLE meal_foods (
    meal_id INT NOT NULL,
    food_id INT NOT NULL,
    PRIMARY KEY(meal_id, food_id),
    FOREIGN KEY(meal_id) REFERENCES meals(meal_id) ON DELETE CASCADE,
    FOREIGN KEY(food_id) REFERENCES foods(food_id) ON DELETE CASCADE
) COMMENT='식단 구성을 위한 교차 테이블';

-- 4. students (학생 정보)
CREATE TABLE students (
    student_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(20) NOT NULL,
    birth_date DATE,
    phone_number VARCHAR(15),
    gender ENUM('F', 'M')
) COMMENT='학생 마스터 정보';

-- 5. accounts (계정 정보)
CREATE TABLE accounts (
    student_id VARCHAR(10) PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
) COMMENT='로그인 인증 정보';

-- 6. reviews (리뷰 정보)
CREATE TABLE reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    meal_id INT NOT NULL,
    student_id VARCHAR(10) NOT NULL,
    rating FLOAT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_comment TEXT,
    photo_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(meal_id, student_id),
    FOREIGN KEY(meal_id) REFERENCES meals(meal_id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
) COMMENT='학생들의 식단 리뷰';

-- 7. statistics (평점 통계 및 AI 분석) [신규 추가]
CREATE TABLE statistics (
    stat_id INT AUTO_INCREMENT PRIMARY KEY,
    period_type ENUM('WEEKLY', 'MONTHLY') NOT NULL, -- 주차별/월별 구분
    period_value VARCHAR(20) NOT NULL, -- 예: '2024-05-W1' 또는 '2024-05'
    avg_rating DECIMAL(3,2), -- 평균 평점
    ai_comment TEXT, -- AI 평점 분석 코멘트 (LLM 결과 저장용)
    total_reviews INT DEFAULT 0, -- 해당 기간 총 리뷰 수
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(period_type, period_value)
) COMMENT='AI 분석 코멘트 및 정기 통계 데이터';