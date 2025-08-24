# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 데이터베이스 엔진과 Base를 로드합니다.
from database.database import engine, Base

# 라우터들을 가져옵니다.
from route.auth import auth_router
from route.token import router as token_router
from route.thread import threads_router
from route.message import router as message_router
from route.model import model_router
from route.user import user_router
# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 라우트 등록
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(token_router)
app.include_router(threads_router)
app.include_router(message_router)
app.include_router(model_router)

# CORS 설정 (필요하다면 allow_origins를 도메인 목록으로 변경)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}
