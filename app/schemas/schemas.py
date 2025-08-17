from pydantic import BaseModel, EmailStr
import datetime

# --- User ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone_number: str | None = None # 휴대폰 번호는 선택적으로 받도록 변경

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime.datetime

    class Config:
        from_attributes = True # orm_mode 대신 from_attributes 사용

# --- Token ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
