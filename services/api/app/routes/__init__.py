from fastapi import APIRouter
from app.routes import users, meals, auth, reviews, statistics

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(meals.router, prefix="/meals", tags=["meals"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["statistics"])
