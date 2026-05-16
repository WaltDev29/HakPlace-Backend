import uvicorn
from app import create_app
from app.db.session import engine, Base

# 테이블 생성은 수동으로 진행 (create_tables.sql 사용)
# Base.metadata.create_all(bind=engine)

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
