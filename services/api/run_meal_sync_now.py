import os
import sys

# 프로젝트 루트를 PYTHONPATH에 추가하여 패키지 임포트 지원
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tasks.meal_sync import crawl_and_sync

if __name__ == "__main__":
    print("\n" + "="*60)
    print(" 🚀 [FORCE RUN] 학식 데이터 강제 동기화 실행")
    print("="*60)
    crawl_and_sync()
