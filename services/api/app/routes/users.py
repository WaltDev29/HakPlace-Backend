from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Student
from app.schemas.user import UserInfo
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/me", response_model=UserInfo, summary="내 정보 조회", description="현재 로그인된 사용자의 상세 정보를 조회합니다.")
def read_user_me(current_user: Student = Depends(get_current_user)):
    """
    내 정보 조회 (리뷰 목록 미포함)
    """
    return current_user

@router.get("/{student_id}", response_model=UserInfo, summary="특정 학생 정보 조회", description="특정 학번을 가진 학생의 정보를 조회합니다. 본인 정보만 조회 가능하도록 제한되어 있습니다.")
def read_user_by_id(student_id: str, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    """
    특정 학생 정보 조회
    """
    if student_id != current_user.student_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
    user = db.query(Student).filter(Student.student_id == student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, summary="회원 탈퇴", description="현재 로그인된 사용자의 계정과 모든 관련 데이터를 삭제합니다.")
def delete_user_me(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    """
    회원 탈퇴
    """
    db.delete(current_user)
    db.commit()
    return None
