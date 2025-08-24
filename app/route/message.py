from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from database import get_db
from models import Thread, Message, Users
from utils import get_current_user, WSConnectionManager, authenticate_websocket, own_thread
from schemas import MessageOut, MessageCreate


router = APIRouter(prefix="/threads", tags=["messages"])

# ---------------------------------------------------------------------
# REST: 목록 조회 (온디바이스 구조 - 서버는 저장/조회 전용)
# ---------------------------------------------------------------------
@router.get("/{thread_id}/messages",response_model=List[MessageOut],operation_id="list_messages_v2",)
def list_messages(thread: Thread = Depends(own_thread), db: Session = Depends(get_db), limit: int = Query(50, ge=1, le=200), before_id: Optional[int] = None,):
    q = db.query(Message).filter(Message.thread_id == thread.thread_id)
    if before_id is not None:
        q = q.filter(Message.message_id < before_id)
    rows = q.order_by(Message.message_id.desc()).limit(limit).all()
    return list(reversed(rows))  # 최신이 위로 쌓이지만 클라 편의를 위해 역순 반환

@router.get("/{thread_id}/messages/{message_id}",response_model=MessageOut,operation_id="get_message_v2",)
def get_message(thread: Thread = Depends(own_thread), message_id: int = 0, db: Session = Depends(get_db),):
    row = (db.query(Message).filter(Message.thread_id == thread.thread_id, Message.message_id == message_id).first())
    if not row:
        raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다.")
    return row

@router.post("/{thread_id}/messages",response_model=MessageOut,operation_id="create_message_v2",)
def create_message(body: MessageCreate, thread: Thread = Depends(own_thread), user: Users = Depends(get_current_user), db: Session = Depends(get_db),):
    # 서버는 모델 호출을 하지 않음. 단순히 저장만.
    row = Message(thread_id=thread.thread_id, user_id=user.user_id if body.role == "user" else thread.user_id, role=body.role,
        content=body.content, client_message_id=getattr(body, "client_message_id", None), meta=getattr(body, "meta", None),)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

# ---------------------------------------------------------------------
# WebSocket: 실시간 이벤트 브로드캐스트 (chat/typing/read/system)
# ---------------------------------------------------------------------
manager = WSConnectionManager()

@router.websocket("/ws/{thread_id}")
async def ws_chat(websocket: WebSocket, thread_id: int, db: Session = Depends(get_db)):
    # 클라이언트는 ws://.../threads/ws/{thread_id}?token=JWT 로 접속
    user_id = await authenticate_websocket(websocket, db, thread_id)
    await manager.connect(thread_id, websocket)

    # 참여 알림
    try:
        await manager.broadcast(
            thread_id,
            json.dumps({"type": "system", "event": "joined", "user_id": user_id}),
        )

        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "invalid_json"}))
                continue

            evt_type = data.get("type")
            if evt_type not in {"chat", "typing", "read"}:
                await websocket.send_text(json.dumps({"type": "error", "message": "unknown_type"}))
                continue

            # 그대로 브로드캐스트 (서버는 단순 중계)
            await manager.broadcast(thread_id, json.dumps(data))

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(thread_id, websocket)
        await manager.broadcast(
            thread_id,
            json.dumps({"type": "system", "event": "left", "user_id": user_id}),
        )
