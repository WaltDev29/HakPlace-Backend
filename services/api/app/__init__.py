from fastapi import FastAPI
from app.routes import api_router
from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks.meal_sync import crawl_and_sync
import logging

def create_app() -> FastAPI:
    app = FastAPI(
        title="HakPlace API",
        description="HakPlace Backend Service",
        version="1.0.0"
    )

    # 라우터 등록
    app.include_router(api_router)

    # 스케줄러 설정 (평일 08:00 실행)
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        crawl_and_sync, 
        'cron', 
        day_of_week='mon-fri', 
        hour=8, 
        minute=0,
        id='meal_sync_task'
    )
    scheduler.start()
    logging.info("배치 스케줄러 시작: 평일 08:00 크롤링 예약됨")

    @app.on_event("shutdown")
    def shutdown_event():
        scheduler.shutdown()

    @app.get("/")
    async def root():
        return {"message": "Welcome to HakPlace API"}

    return app
