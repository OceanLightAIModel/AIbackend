from sqlalchemy import Column, Integer, String, DateTime
import datetime
from sqlalchemy.orm import relationship
from database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # RefreshToken 모델과의 관계: 한 사용자가 여러 리프레시 토큰을 가질 수 있음
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def user_id(self) -> int:
        return self.id

