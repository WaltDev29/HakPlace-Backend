import base64
import os
import uuid
import magic
from pathlib import Path

# 이미지 저장 경로 설정
UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_base64_image(base64_str: str) -> str:
    """
    Base64 이미지를 검증 후 파일로 저장하고 URL 경로를 반환합니다.
    """
    try:
        # data:image/png;base64,... 형식 처리
        if "," in base64_str:
            header, base64_str = base64_str.split(",")
            
        img_data = base64.b64decode(base64_str)
        
        # MIME 타입 체크
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(img_data)
        
        if not file_type.startswith("image/"):
            print(f"허용되지 않는 파일 형식: {file_type}")
            return None
            
        # 확장자 결정
        ext = file_type.split("/")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = UPLOAD_DIR / filename
        
        with open(file_path, "wb") as f:
            f.write(img_data)
            
        return f"/static/uploads/{filename}"
    except Exception as e:
        print(f"이미지 저장 오류: {e}")
        return None
