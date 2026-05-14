from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Student, Account
from app.schemas.user import UserSignup, Token
from app.core.security import get_password_hash, verify_password, create_access_token
from datetime import datetime, timedelta
from typing import Dict

router = APIRouter()

# 로그인 시도 제한을 위한 메모리 저장소 (실무에서는 Redis 권장)
# { "student_id": {"count": 0, "block_until": datetime} }
login_attempts: Dict[str, dict] = {}

@router.post("/signup", status_code=status.HTTP_201_CREATED, summary="회원가입", description="관리자가 사전 등록한 students 테이블의 정보(학번, 이름, 생년월일, 성별, 전화번호)와 일치할 경우에만 계정을 생성합니다. 전화번호는 하이픈 유무와 관계없이 대조합니다.")
def signup(user_in: UserSignup, db: Session = Depends(get_db)):
    # 1. 학생 정보가 사전 등록되어 있는지 확인
    student = db.query(Student).filter(Student.student_id == user_in.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="가입 정보를 확인해주세요. 등록되지 않은 학번이거나 입력값이 올바르지 않습니다."
        )
    
    # 2. 이미 계정이 생성되어 있는지 확인
    existing_account = db.query(Account).filter(Account.student_id == user_in.student_id).first()
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 가입된 학번입니다."
        )
    
    # 3. 상세 정보 일치 확인 (이름, 생년월일, 성별, 전화번호)
    # 전화번호는 하이픈 제외하고 비교
    def clean_phone(phone: str) -> str:
        return phone.replace("-", "") if phone else ""

    # 디버깅용 로그 (실제 서비스에서는 민감 정보이므로 주의)
    print(f"DEBUG: Comparing student_id={user_in.student_id}")
    print(f"DEBUG: Name match: DB='{student.name}', Input='{user_in.name}' -> {student.name == user_in.name}")
    print(f"DEBUG: Birth match: DB='{student.birth_date}', Input='{user_in.birth_date}' -> {student.birth_date == user_in.birth_date}")
    print(f"DEBUG: Gender match: DB='{student.gender}', Input='{user_in.gender}' -> {student.gender == user_in.gender}")
    print(f"DEBUG: Phone match: DB='{clean_phone(student.phone_number)}', Input='{clean_phone(user_in.phone_number)}' -> {clean_phone(student.phone_number) == clean_phone(user_in.phone_number)}")

    is_info_match = (
        student.name == user_in.name and
        student.birth_date == user_in.birth_date and
        student.gender == user_in.gender and
        clean_phone(student.phone_number) == clean_phone(user_in.phone_number)
    )

    if not is_info_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="학생 정보가 일치하지 않습니다. 입력한 정보를 다시 확인해주세요."
        )
    
    # 4. 계정 생성 (학생 정보는 기존 것 유지)
    new_account = Account(
        student_id=user_in.student_id,
        password_hash=get_password_hash(user_in.password)
    )
    db.add(new_account)
    
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="회원가입 처리 중 오류가 발생했습니다."
        )
    
    return {"message": "회원가입이 완료되었습니다."}

@router.post("/login", response_model=Token, summary="로그인", description="학번과 비밀번호를 통해 액세스 토큰을 발급받습니다. 5회 이상 실패 시 5분간 차단됩니다.")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    student_id = form_data.username
    now = datetime.now()

    # 로그인 시도 제한 확인
    attempt = login_attempts.get(student_id, {"count": 0, "block_until": now})
    if attempt["block_until"] > now:
        remaining = int((attempt["block_until"] - now).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"너무 많은 로그인 시도가 있었습니다. {remaining}초 후에 다시 시도해주세요."
        )

    account = db.query(Account).filter(Account.student_id == student_id).first()
    
    if not account or not verify_password(form_data.password, account.password_hash):
        # 로그인 실패 시 카운트 증가
        attempt["count"] += 1
        if attempt["count"] >= 5: # 5회 실패 시
            attempt["block_until"] = now + timedelta(minutes=5) # 5분간 차단
            attempt["count"] = 0 # 차단 후 카운트 초기화
        
        login_attempts[student_id] = attempt
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="학번 또는 비밀번호가 일치하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 로그인 성공 시 시도 횟수 초기화
    if student_id in login_attempts:
        del login_attempts[student_id]
    
    access_token = create_access_token(subject=account.student_id)
    return {"access_token": access_token, "token_type": "bearer"}
