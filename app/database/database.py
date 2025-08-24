# app/database/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os, time
from database.base import Base

DB_USER = os.getenv("OCEAN_USER")
DB_PASSWORD = os.getenv("OCEAN_DB_USER_PASSWORD")
DB_HOST = os.getenv("OCEAN_DB_HOST")
DB_PORT = os.getenv("OCEAN_DB_PORT")
DB_NAME = os.getenv("OCEAN_DB")

SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = None
for _ in range(5):
    try:
        # 커넥션 풀 관련 옵션 추가
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_pre_ping=True,    # 연결 사용할 때마다 ping으로 유휴 연결 체크
            pool_recycle=3600,     # 1시간마다 커넥션을 재생성 (타임아웃 방지)
            pool_size=10,          # 기본 커넥션 수
            max_overflow=20,       # 부족할 때 추가로 생성할 커넥션 수
        )
        engine.connect()
        print("DB 연결 성공")
        break
    except Exception as e:
        print("DB 연결 실패:", e)
        time.sleep(2)

if engine is None:
    print("DB 최종 연결 실패. 서버를 종료합니다.")
    exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
