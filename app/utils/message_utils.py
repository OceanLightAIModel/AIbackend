
from fastapi import Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Set
import os

from database import get_db
from models import Thread, Users
from utils import AuthHandler, get_current_user  
from schemas import MessageOut, MessageCreate

# ---------------------------------------------------------------------
# 공용 유틸 (온디바이스 구조 기준)
# ---------------------------------------------------------------------

def messages_to_prompt(messages: List[Dict[str, str]]) -> str:
    # 온디바이스에서 필요하면 클라이언트 쪽에서 프롬프트를 구성하고,
    # 서버는 굳이 사용할 필요는 없음. 호환을 위해 단순 포맷만 남김.
    lines = [f"{m.get('role','')}: {m.get('content','')}" for m in messages]
    lines.append("assistant:")
    return "\n".join(lines)

def assert_thread_ownership(db: Session, thread_id: int, user_id: int) -> Thread:
    thread = (
        db.query(Thread)
        .filter(Thread.thread_id == thread_id, Thread.user_id == user_id)
        .first()
    )
    if not thread:
        raise HTTPException(status_code=404, detail="스레드를 찾을 수 없거나 권한이 없습니다.")
    return thread

def own_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user),
) -> Thread:
    return assert_thread_ownership(db, thread_id, user.user_id)

# ---------------------------------------------------------------------
# WebSocket helpers
# ---------------------------------------------------------------------

class WSConnectionManager:
    def __init__(self):
        self.rooms: Dict[int, Set[WebSocket]] = {}

    async def connect(self, thread_id: int, websocket: WebSocket):
        await websocket.accept()
        self.rooms.setdefault(thread_id, set()).add(websocket)

    def disconnect(self, thread_id: int, websocket: WebSocket):
        conns = self.rooms.get(thread_id)
        if not conns:
            return
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self.rooms.pop(thread_id, None)

    async def broadcast(self, thread_id: int, message: str):
        for ws in list(self.rooms.get(thread_id, [])):
            try:
                await ws.send_text(message)
            except Exception:
                # 실패 소켓 정리
                self.disconnect(thread_id, ws)

async def authenticate_websocket(websocket: WebSocket, db: Session, thread_id: int) -> int:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401, detail="토큰이 필요합니다.")

    try:
        user_id = AuthHandler().decode_token(token)["user_id"]
    except Exception:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    assert_thread_ownership(db, thread_id, user_id)
    return user_id
