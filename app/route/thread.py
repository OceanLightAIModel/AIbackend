from fastapi import APIRouter, Depends, FastAPI, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from models import Thread, Message, Users
from database import get_db
from utils import get_current_user
from schemas import ThreadCreate, ThreadUpdate, ThreadResponse, ThreadDetail
import uuid


threads_router = APIRouter(prefix="/threads", tags=["threads"])

connected_clients = []


#######################################################
####################### Threads #######################
#######################################################

### 스레드 생성 ###
@threads_router.post("/threads", response_model=ThreadDetail)
def create_thread(body: ThreadCreate, db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    threads = Thread(user_id=user.user_id, thread_title=body.thread_title)
    try:
        db.add(threads)
        db.commit()
        db.refresh(threads)
        return threads
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="스레드 생성 중 오류가 발생했습니다.")

### 스레드 리스트 및 페이지네이션 ###
@threads_router.get("/threads", response_model=List[ThreadResponse])
def list_threads(db: Session=Depends(get_db), user: Users = Depends(get_current_user), limit: int = Query(20, ge=1, le=100), 
                 before_id: Optional[int] = Query(None, description="스레드 ID보다 작은 스레드만 조회"),):
    
    threads = db.query(Thread).filter(Thread.user_id == user.user_id)
    if before_id is not None:
        threads = threads.filter(Thread.thread_id < before_id)

    rows = (
        threads.order_by(Thread.thread_id.desc()).limit(limit).all())
    return rows

### 자신의 스레드 조회  ###
@threads_router.get("/threads/{thread_id}", response_model=ThreadDetail)
def get_thread(thread_id: int, db: Session = Depends(get_db), user: Users = Depends(get_current_user),):
    threads = db.query(Thread).filter(Thread.thread_id == thread_id, Thread.user_id == user.user_id).first()
    if not threads:
        raise HTTPException(status_code=404, detail="스레드를 찾을 수 없습니다.")
    return threads

### 스레드 이름 수정 ###
@threads_router.patch("/threads/{thread_id}", response_model=ThreadDetail)
def update_thread(thread_id: int, body: ThreadUpdate, db: Session = Depends(get_db), user: Users = Depends(get_current_user),):
    threads = db.query(Thread).filter(Thread.thread_id == thread_id, Thread.user_id == user.user_id).first()
    if not threads:
        raise HTTPException(status_code=404, detail="스레드를 찾을 수 없습니다.")
    
    changed = False
    if body.thread_title is not None:
        threads.thread_title = body.thread_title
        changed = True

    if changed:
        try:
            db.commit()
            db.refresh(threads)
            return threads
        except:
            db.rollback()
            raise HTTPException(status_code=500, detail="스레드 수정 중 오류가 발생했습니다.")

### 스레드 삭제 ###
@threads_router.delete("/threads/{thread_id}")
def delete_thread(thread_id: int, db: Session = Depends(get_db), user: Users = Depends(get_current_user),):
    threads = db.query(Thread).filter(Thread.thread_id == thread_id, Thread.user_id == user.user_id).first()
    if not threads:
        raise HTTPException(status_code=404, detail="스레드를 찾을 수 없습니다.")
    try:
        db.delete(threads)
        db.commit()
        return {"detail": "스레드가 삭제되었습니다."}
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="스레드 삭제 중 오류가 발생했습니다.")
