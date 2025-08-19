from passlib.context import CryptContext
import os
import hmac
import hashlib
from typing import Optional

# 패스워드 해싱에 사용할 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# .env의 토큰 페퍼를 읽어옴
TOKEN_PEPPER = os.getenv("TOKEN_PEPPER", "")

def hash_password(password: str) -> str:
    """
    비밀번호를 해싱합니다.
    """
    return pwd_context.hash(password)

# 과거 코드와 호환을 위해 별칭을 추가합니다.
# get_password_hash를 호출하면 hash_password를 실행합니다.
def get_password_hash(password: str) -> str:
    """
    비밀번호를 해싱합니다. (호환용)
    """
    return hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호가 일치하는지 검증합니다.
    """
    return pwd_context.verify(plain_password, hashed_password)

def _token_hash(token: str) -> str:
    """
    HMAC을 이용해 토큰을 해싱합니다.
    """
    return hmac.new(TOKEN_PEPPER.encode(), token.encode(), hashlib.sha256).hexdigest()
