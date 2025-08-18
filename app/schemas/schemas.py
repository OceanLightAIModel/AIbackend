from pydantic import BaseModel, EmailStr
import datetime

# --- User ---
class UserCreate(BaseModel):
    """사용자 생성 요청 스키마."""
    username: str
    email: EmailStr
    password: str
    phone_number: str | None = None  # 휴대폰 번호는 선택 입력

# 호환성을 위한 별칭: UserRegister = UserCreate
UserRegister = UserCreate

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    phone_number: str | None = None
    created_at: datetime.datetime
    class Config:
        from_attributes = True  # Pydantic이 ORM 모델을 받아들일 수 있도록 설정

# --- Token ---
class Token(BaseModel):
    """엑세스/리프레시 토큰 응답 스키마."""
    access_token: str
    refresh_token: str
    token_type: str

# 호환성을 위한 별칭: TokenResponse = Token
TokenResponse = Token

class TokenData(BaseModel):
    """토큰 페이로드에서 email 등의 추가 정보를 표현."""
    email: str | None = None

# 로그인 요청 시 사용할 수 있는 스키마 예시
class Login(BaseModel):
    email: EmailStr
    password: str
