# app/route/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from database.database import get_db
from schemas import UserCreate, UserResponse, Token, UserPreferenceUpdate
from models import User
from utils.hash_utils import get_password_hash, verify_password
from utils.token_utils import auth_handler, get_current_user

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    신규 회원 가입 엔드포인트.
    - 이메일 중복 검사를 수행하고
    - 비밀번호를 해싱하여 저장합니다.
    - phone_number, chat_theme, dark_mode는 선택적입니다.
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        chat_theme=user.chat_theme if user.chat_theme is not None else False,
        dark_mode=user.dark_mode if user.dark_mode is not None else False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@auth_router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    로그인 엔드포인트.
    - form_data.username에는 이메일이 들어옵니다.
    - 비밀번호 검증 후 access/refresh 토큰을 발급합니다.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_handler.create_access_token(user.user_id)
    refresh_token = auth_handler.create_refresh_token(user.user_id)
    auth_handler.save_token(db, user.user_id, refresh_token)
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@auth_router.put("/preference", response_model=UserResponse)
def update_preference(
    preference: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),  # 함수 의존성 주입
    db: Session = Depends(get_db),
):
    if preference.chat_theme is not None:
        current_user.chat_theme = preference.chat_theme
    if preference.dark_mode is not None:
        current_user.dark_mode = preference.dark_mode
    db.commit()
    db.refresh(current_user)
    return current_user
