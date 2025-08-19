# app/schemas/schemas.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import datetime

# --- User ---
class UserCreate(BaseModel):
    """사용자 생성 요청 스키마."""
    username: str
    email: EmailStr
    password: str 

# 호환성을 위한 별칭
UserRegister = UserCreate

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    created_at: datetime.datetime

    class Config:
        orm_mode = True  # SQLAlchemy 모델을 응답으로 사용할 수 있도록 설정

# --- Token ---
class Token(BaseModel):
    """엑세스/리프레시 토큰 응답 스키마."""
    access_token: str
    refresh_token: str
    token_type: str

# 호환성을 위한 별칭
TokenResponse = Token

class TokenData(BaseModel):
    """토큰 페이로드에서 email 등의 추가 정보를 표현."""
    email: Optional[str] = None

# 로그인 요청 시 사용할 스키마
class Login(BaseModel):
    email: EmailStr
    password: str

# --- Thread ---
class ThreadCreate(BaseModel):
    thread_title: str = Field(..., description="스레드 제목")

class ThreadUpdate(BaseModel):
    thread_title: str = Field(..., description="스레드 제목")

class ThreadResponse(BaseModel):
    thread_id: int = Field(..., description="스레드 ID")
    thread_title: str = Field(..., description="스레드 제목")
    created_at: datetime.datetime = Field(..., description="스레드 생성 시간")

    class Config:
        orm_mode = True

class ThreadDetail(BaseModel):
    thread_id: int
    thread_title: str
    user_id: int
    created_at: datetime.datetime

    class Config:
        orm_mode = True

# --- Message ---
class MessageResponse(BaseModel):
    message_id: int
    thread_id: int
    user_id: int
    content: str
    created_at: datetime.datetime

    class Config:
        orm_mode = True

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000)
    # 멱등/중복 전송 방지용 (client_message_id가 동일하면 같은 요청으로 처리)
    client_message_id: Optional[str] = None
    stream: bool = False  # HTTP에서 스트리밍 대신 최종본만 받을지 선택

class MessageOut(BaseModel):
    message_id: int
    thread_id: int
    sender_type: str
    content: str
    created_at: datetime.datetime

    class Config:
        orm_mode = True
