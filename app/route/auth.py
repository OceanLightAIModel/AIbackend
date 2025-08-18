from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from database.database import get_db
from schemas import UserCreate, UserResponse, Token
from models import User
from utils.hash_utils import get_password_hash, verify_password
from utils.token_utils import auth_handler

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@auth_router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # 이메일 중복 체크
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    # 비밀번호 해싱 후 사용자 생성
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        phone_number=user.phone_number,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@auth_router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # email이 form_data.username에 매핑됩니다.
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
       )
    # 토큰 생성
    access_token = auth_handler.create_access_token(user.user_id)
    refresh_token = auth_handler.create_refresh_token(user.user_id)
    # 새 리프레시 토큰을 저장
    db_token = auth_handler.save_token(db, user.user_id, refresh_token)
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
