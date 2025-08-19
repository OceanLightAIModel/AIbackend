from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import time
from database.base import Base  # Base를 database/base.py에서 가져옵니다

# 환경 변수 로드
DB_USER = os.getenv("OCEAN_USER")
DB_PASSWORD = os.getenv("OCEAN_DB_USER_PASSWORD")
DB_HOST = os.getenv("OCEAN_DB_HOST")
DB_PORT = os.getenv("OCEAN_DB_PORT")
DB_NAME = os.getenv("OCEAN_DB")

# SQLAlchemy 연결 문자열
SQLALCHEMY_DATABASE_URL = (
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# DB 연결 시도 (재시도 로직)
engine = None
for i in range(5):
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        engine.connect()
        print("DB 연결 성공")
        break
    except Exception as e:
        print(f"DB 연결 실패 ({type(e).__name__}) {e}")
        time.sleep(2)

if engine is None:
    print("DB 최종 연결 실패. 서버를 종료합니다.")
    exit(1)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """요청 처리 시마다 데이터베이스 세션을 제공하는 제너레이터."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
