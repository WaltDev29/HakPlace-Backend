from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import api_router
from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks.meal_sync import crawl_and_sync
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

def create_app() -> FastAPI:
    app = FastAPI(
        title="🍱 HakPlace API",
        description="""
학식 앱 **HakPlace**를 위한 백엔드 API 서비스입니다.

### 제공 기능
* **Auth**: 회원가입, JWT 로그인 및 보안 강화
* **Meals**: 일간/주간 식단 정보 조회
* **Reviews**: 식단별 리뷰 작성, 이미지 업로드, 실시간 평점 반영
* **Statistics**: AI 기반 식단 분석 및 통계 제공
* **Users**: 내 정보 관리 및 계정 탈퇴
        """,
        version="1.1.0",
        contact={
            "name": "HakPlace Team",
            "url": "https://github.com/WaltDev29/HakPlace-Backend",
        },
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 및 정적 파일 설정
    app.include_router(api_router)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # 스케줄러 설정
    scheduler = BackgroundScheduler()
    
    # 1. 식단 동기화 (평일 08:00 실행)
    scheduler.add_job(
        crawl_and_sync, 
        'cron', 
        day_of_week='mon-fri', 
        hour=8, 
        minute=0,
        id='meal_sync_task'
    )
    
    # 2. 음식별 평점 캐싱 (1시간마다 실행)
    from app.tasks.food_stats import update_food_ratings
    scheduler.add_job(
        update_food_ratings,
        'interval',
        hours=1,
        id='food_stats_update_task',
        next_run_time=datetime.now() # 시작 시 즉시 실행
    )
    
    # 3. AI 리뷰 분석 (평일 08:00)
    from app.tasks.stat_tasks import update_weekly_stats, run_saturday_stats
    scheduler.add_job(
        update_weekly_stats,
        'cron',
        day_of_week='mon-fri',
        hour=8,
        minute=0,
        id='weekly_ai_analysis_task'
    )

    # 4. 주간 최종 및 월간 통합 분석 (토요일 08:00)
    scheduler.add_job(
        run_saturday_stats,
        'cron',
        day_of_week='sat',
        hour=8,
        minute=0,
        id='saturday_ai_analysis_task'
    )
    
    scheduler.start()
    logging.info("배치 스케줄러 시작: 식단 동기화(평일 08:00) 및 음식 통계(1시간 주기) 예약됨")

    @app.on_event("shutdown")
    def shutdown_event():
        scheduler.shutdown()

    # 스케줄러 설정
    scheduler = BackgroundScheduler()
    
    # 1. 식단 동기화 (평일 08:00 실행)
    scheduler.add_job(
        crawl_and_sync, 
        'cron', 
        day_of_week='mon-fri', 
        hour=8, 
        minute=0,
        id='meal_sync_task'
    )
    
    # 2. 음식별 평점 캐싱 (1시간마다 실행)
    from app.tasks.food_stats import update_food_ratings
    scheduler.add_job(
        update_food_ratings,
        'interval',
        hours=1,
        id='food_stats_update_task',
        next_run_time=datetime.now() # 시작 시 즉시 실행
    )
    
    # 3. AI 리뷰 분석 (평일 08:00)
    from app.tasks.stat_tasks import update_weekly_stats, run_saturday_stats
    scheduler.add_job(
        update_weekly_stats,
        'cron',
        day_of_week='mon-fri',
        hour=8,
        minute=0,
        id='weekly_ai_analysis_task'
    )

    # 4. 주간 최종 및 월간 통합 분석 (토요일 08:00)
    scheduler.add_job(
        run_saturday_stats,
        'cron',
        day_of_week='sat',
        hour=8,
        minute=0,
        id='saturday_ai_analysis_task'
    )
    
    scheduler.start()
    logging.info("배치 스케줄러 시작: 식단 동기화(평일 08:00) 및 음식 통계(1시간 주기) 예약됨")

    @app.on_event("shutdown")
    def shutdown_event():
        scheduler.shutdown()

    @app.get("/")
    async def root():
        return {"message": "Welcome to HakPlace API"}

    return app
