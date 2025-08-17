from sqlalchemy import Column, Integer, String, DateTime
import datetime
# 'database.database' 대신 'database.base'에서 Base를 가져옵니다.
from database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
