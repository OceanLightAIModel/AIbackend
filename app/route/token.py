from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from utils.token_utils import auth_handler
from utils.hash_utils import _token_hash
from models import RefreshToken

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """리프레시 토큰을 사용해 새로운 엑세스/리프레시 토큰을 발급합니다."""
    payload = auth_handler.verify_refresh_token(db, refresh_token)
    user_id = int(payload["sub"])
    new_access, new_refresh = auth_handler.rotate_refresh_token(db, refresh_token, user_id)
    db.commit()
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(refresh_token: str, db: Session = Depends(get_db)):
    """리프레시 토큰을 폐기하고 로그아웃 처리합니다."""
    token_hash = _token_hash(refresh_token)
    token_record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if token_record:
        token_record.revoked = True
        db.commit()
    return {"detail": "로그아웃되었습니다."}
