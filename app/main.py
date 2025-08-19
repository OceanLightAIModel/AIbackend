from fastapi import FastAPI
<<<<<<< HEAD
from starlette.middleware.cors import CORSMiddleware
from database.database import engine, Base
from route.auth import auth_router
from route.token import router as token_router
=======
from fastapi.middleware.cors import CORSMiddleware
from database import get_db, engine, base
from models import base
from route import auth_router, threads_router, message_router 

>>>>>>> d21e0d7 (update)

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()
<<<<<<< HEAD
=======
app.include_router(auth_router)
app.include_router(threads_router)
app.include_router(message_router)
>>>>>>> d21e0d7 (update)

# CORS 설정: 필요에 따라 제한 가능
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
# 라우트 등록
app.include_router(auth_router)
app.include_router(token_router)

=======
#base.metadata.create_all(bind=engine) #DB 처음 생성할 때만 사용, DB 테이블이 이미 존재하면 오류 발생
>>>>>>> d21e0d7 (update)

@app.get("/")
def read_root():
    return {"Hello": "World"}

