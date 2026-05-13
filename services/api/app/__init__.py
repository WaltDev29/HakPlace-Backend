from fastapi import FastAPI
from app.routes import api_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="HakPlace API",
        description="HakPlace Backend Service",
        version="1.0.0"
    )

    # 라우터 등록
    app.include_router(api_router)

    @app.get("/")
    async def root():
        return {"message": "Welcome to HakPlace API"}

    return app
