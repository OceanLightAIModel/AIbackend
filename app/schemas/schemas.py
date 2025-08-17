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
    """사용자 응답 스키마."""
    id: int
    username: str
    email: EmailStr
    created_at: datetime.datetime

    class Config:
        # orm_mode 대신 from_attributes 사용
        from_attributes = True

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
