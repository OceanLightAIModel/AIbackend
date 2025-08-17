from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import time

# .env 파일에서 환경 변수 로드
DB_USER = os.getenv("OCEAN_USER")
DB_PASSWORD = os.getenv("OCEAN_DB_USER_PASSWORD")
DB_HOST = os.getenv("OCEAN_DB_HOST")
DB_PORT = os.getenv("OCEAN_DB_PORT")
DB_NAME = os.getenv("OCEAN_DB")

# SQLAlchemy 연결 문자열 생성
SQLALCHEMY_DATABASE_URL = (
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# DB 연결 시도 (재시도 로직 포함)
engine = None
for i in range(5):  # 최대 5번 재시도
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        engine.connect()
        print("DB 연결 성공")
        break
    except Exception as e:
        print(f"DB 연결 실패 ({type(e).__name__}) {e}")
        time.sleep(2)  # 2초 대기 후 재시도

if engine is None:
    print("DB 최종 연결 실패. 서버를 종료합니다.")
    exit(1)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy 모델을 위한 Base 클래스 정의
Base = declarative_base()

def get_db():
    """요청 처리 시마다 데이터베이스 세션을 제공하는 제너레이터 함수."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
