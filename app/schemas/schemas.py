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
<<<<<<< HEAD
=======
    
    @validator("identifier")
    def validate_identifier(cls, v):
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if re.fullmatch(email_regex, v):
            return {"type": "email", "value": v}

        # 형식이 잘못된 경우 예외 발생
        raise ValueError("identifier는 유효한 이메일 또는 전화번호여야 합니다.")
    

class ThreadCreate(BaseModel):
    thread_title: str = Field(..., description="스레드 제목")

class ThreadUpdate(BaseModel):
    thread_title: str = Field(..., description="스레드 제목")

class ThreadResponse(BaseModel):
    thread_id: int = Field(..., description="스레드 ID")
    thread_title: str = Field(..., description="스레드 제목")
    created_at: datetime = Field(..., description="스레드 생성 시간")

    class Config:
        orm_mode = True

class ThreadDetail(BaseModel):
    thread_id: int
    thread_title: str
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class MessageResponse(BaseModel):
    message_id: int
    thread_id: int
    user_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True        

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000)
    # 멱등/중복 전송 방지용 (DB에 client_message_id 추가하면 유니크 보장 가능)
    client_message_id: Optional[str] = None
    stream: bool = False  # HTTP에서 스트리밍 대신 최종본만 받을지 선택(WS 권장)

class MessageOut(BaseModel):
    message_id: int
    thread_id: int
    sender_type: str
    content: str
    created_at: datetime

    class Config:
        orm_mode=True
>>>>>>> d21e0d7 (update)
