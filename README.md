# 🍱 HakPlace Backend API

**HakPlace Backend**는 학생들을 위한 학식 정보 제공 및 AI 분석 서비스의 코어 API 엔진입니다.  
FastAPI를 기반으로 설계되었으며, 비동기 크롤링과 LLM(GPT)을 활용한 데이터 분석 파이프라인을 제공합니다.

---

## 🏗 System Architecture

- **API Framework**: FastAPI (Asynchronous Python Framework)
- **Database**: MySQL 8.0 (RDBMS)
- **Task Scheduling**: APScheduler (주기적 식단 동기화 및 통계 생성)
- **Data Scraping**: Playwright (Headless Browser)
- **AI Engine**: OpenAI API (GPT-4 based review analysis)
- **Containerization**: Docker & Docker Compose

## 📂 Project Structure

```text
├── docker/
│   ├── compose/          # Deployment scripts (Docker Compose)
│   └── env/              # Environment templates (.env.example)
├── services/
│   └── api/
│       ├── app/
│       │   ├── api/      # Dependencies (Security, Auth)
│       │   ├── core/     # Global configurations (Security, Logging)
│       │   ├── db/       # Database session & engine
│       │   ├── models/   # SQLAlchemy Models
│       │   ├── routes/   # API Endpoints (Auth, Meals, Reviews, Stats)
│       │   ├── schemas/  # Pydantic Schemas (Request/Response Models)
│       │   ├── services/ # Business Logic (AI Analysis)
│       │   └── tasks/    # Periodic tasks (Crawl, Stat Update)
│       └── main.py       # Application entry point
├── create_tables.sql     # Database Schema DDL
└── import_menus_excel.py  # Utility for bulk data import
```

## 🛠 Core Features

### 1. Automated Data Pipeline
- **Meal Sync**: 매일 오전 8시, `Playwright`를 이용해 학교 홈페이지에서 최신 식단을 크롤링하여 DB를 동기화합니다.

### 2. AI Statistics & Analysis
- **Weekly/Monthly Batch**: 주간/월간 단위로 학생들의 리뷰 데이터를 수집합니다.  
- **Prompt Engineering**: 수집된 평점과 텍스트 리뷰를 LLM에 전달하여 트렌드 분석, 베스트 메뉴 선정, 개선 포인트 제안을 생성합니다.

### 3. Authentication & Security
- **OAuth2 & JWT**: `jose` 라이브러리를 사용한 보안 토큰 발급 및 검증을 수행합니다.
- **Login Protection**: 특정 횟수 이상 로그인 실패 시 메모리 기반의 일시적 차단 로직을 제공합니다.

## 🚀 Installation & Deployment

### Environment Variables
`.env.api.example`과 `.env.db.example`을 참고하여 서버 환경에 맞는 설정을 구성하십시오.  
특히 서버가 하위 경로(Sub-path, 예: `/hakplace/`)에서 구동될 경우, Swagger UI의 `tokenUrl` 호환성을 위해 `root_path` 설정이 필요할 수 있습니다.

### Running with Docker Compose
```bash
cd docker/compose
docker compose up -d --build
```

### Database Initialization
최초 설치 시 아래 명령어로 스키마를 반영하십시오.
```bash
docker exec -i hakplace-db mysql -u [USER] -p[PASSWORD] hakplace_db < create_tables.sql
```

## 📝 API Documentation
- **Swagger UI**: `http://your-domain/docs`
- **ReDoc**: `http://your-domain/redoc`

---
© 2026 HakPlace Team. All rights reserved.
