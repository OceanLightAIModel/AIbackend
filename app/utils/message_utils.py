from fastapi import APIRouter, Depends, Path, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, AsyncGenerator, List
from database import get_db
from models import Thread, Message, Users
from utils import AuthHandler, get_current_user
from schemas import MessageResponse, MessageCreate, MessageOut


async def stream_llm(prompt: str) -> AsyncGenerator[str, None]:
    # TODO: 여기에 실제 LLM SDK의 스트리밍 제너레이터를 연결
    for ch in ["안녕", "하", "세요!"]:
        yield ch

### 스레드가 유저의 것인지 확인하는 함수 ###
def assert_thread_ownership(db: Session, thread_id: int, user_id: int) -> Thread:
    thread = db.query(Thread).filter(Thread.thread_id == thread_id,
                                Thread.user_id == user_id).first()
    if not thread:
        raise HTTPException(404, "스레드를 찾을 수 없거나 권한이 없습니다.")
    return thread

async def own_thread(thread_id: int = Path(..., description="스레드 ID"), db: Session = Depends(get_db), user: Users = Depends(get_current_user),) -> Thread:
    thread = (
        db.query(Thread).filter(Thread.thread_id == thread_id, Thread.user_id == user.user_id).first()
    )
    
    if not thread:
        raise HTTPException(status_code=404, detail="스레드를 찾을 수 없거나 권한이 없습니다.")
    return thread