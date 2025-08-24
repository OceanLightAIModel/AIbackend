# app/route/threads.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models import Users, Thread
from schemas import ThreadCreate, ThreadUpdate, ThreadResponse
from utils.token_utils import get_current_user

thread_router = APIRouter(prefix="/threads", tags=["threads"])

@thread_router.get("", response_model=list[ThreadResponse])
def list_threads(db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)):
    return db.query(Thread).filter(Thread.user_id == current_user.user_id).all()

@thread_router.get("/{thread_id}/messages")
def list_messages(thread_id: int, db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)):
    thread = db.query(Thread).filter(Thread.thread_id == thread_id, Thread.user_id == current_user.user_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="채팅을 찾을 수 없습니다")
    return thread.messages  # ORM 관계로 messages 가져오기

@thread_router.put("/{thread_id}", response_model=ThreadResponse)
def update_thread(thread_id: int, thread_in: ThreadUpdate, db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)):
    thread = db.query(Thread).filter(Thread.thread_id == thread_id, Thread.user_id == current_user.user_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="채팅을 찾을 수 없습니다")
    thread.thread_title = thread_in.thread_title
    db.commit()
    db.refresh(thread)
    return thread

@thread_router.delete("/{thread_id}")
def delete_thread(thread_id: int, db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)):
    thread = db.query(Thread).filter(Thread.thread_id == thread_id, Thread.user_id == current_user.user_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="채팅을 찾을 수 없습니다")
    db.delete(thread)
    db.commit()
    return {"detail": "삭제되었습니다"}

