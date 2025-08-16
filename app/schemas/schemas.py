from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
import re

## 사용자 회원가입 ##
class UserCreate(BaseModel):
    username: str = Field(..., description="사용자 이름")
    email: EmailStr = Field(..., description="사용자 이메일 주소")
    password: str = Field(..., description="사용자 비밀번호")

    class Config:
        from_attributes = True
    
    @validator("password")
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("비밀번호에는 최소 하나의 대문자가 포함되어야 합니다.")
        if not re.search(r"[0-9]", v):
            raise ValueError("비밀번호에는 최소 하나의 숫자가 포함되어야 합니다.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError('비밀번호에는 특수문자가 포함되어야 합니다.')
        return v
    
    @validator("email")
    def validate_email(cls, v: str) -> str:
        if not v:
            raise ValueError("유효한 이메일 주소를 입력하세요.")
        return v

## 사용자 회원가입 반환 ##
class UserRegister(BaseModel):
    username: str = Field(..., description="사용자 이름")
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

## 로그인 ##
class Login(BaseModel):
    email: EmailStr
    password: str

