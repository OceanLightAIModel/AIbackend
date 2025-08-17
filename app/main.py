from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from database.database import engine, Base
from route.auth import auth_router
from route.token import router as token_router

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS 설정: 필요에 따라 제한 가능
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우트 등록
app.include_router(auth_router)
app.include_router(token_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}

