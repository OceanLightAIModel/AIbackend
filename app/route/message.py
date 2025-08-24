from fastapi import APIRouter, Depends, Query, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from schemas import MessageCreate, MessageOut
from database import get_db
from models import Thread, Message, Users
from utils import AuthHandler, get_current_user, assert_thread_ownership, stream_llm, own_thread
from typing import Optional, List
# from sllm import sllm

import anyio



#######################################################
####################### Messages ######################
#######################################################

router = APIRouter(prefix="/threads", tags=["messages"])


# =========================
# 공통 유틸
# =========================
def _query_messages(db: Session, thread_id: int, before_id: Optional[int], limit: int) -> List[Message]:
    q = db.query(Message).filter(Message.thread_id == thread_id)
    if before_id is not None:
        q = q.filter(Message.message_id < before_id)
    rows = q.order_by(Message.message_id.desc()).limit(limit).all()
    return rows


# =========================
# HTTP: 메시지 목록 (페이지네이션)
# =========================
@router.get("/{thread_id}/messages", response_model=List[MessageOut])
def list_messages(
    thread: Thread = Depends(own_thread),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    before_id: Optional[int] = Query(None, description="이 ID보다 작은 메시지"),
):
    return _query_messages(db, thread.thread_id, before_id, limit)


# =========================
# HTTP: 메시지 단건 조회
# =========================
@router.get("/{thread_id}/messages/{message_id}", response_model=MessageOut)
def get_message(
    message_id: int,
    thread: Thread = Depends(own_thread),
    db: Session = Depends(get_db),
):
    m = (
        db.query(Message)
        .filter(
            Message.thread_id == thread.thread_id,
            Message.message_id == message_id,
        )
        .first()
    )
    if not m:
        raise HTTPException(404, "메시지를 찾을 수 없습니다.")
    return m


# =========================
# HTTP: 메시지 생성 (멱등 + 트랜잭션 롤백)
# - 클라이언트는 body.client_message_id 를 반드시 같이 보냄
# - 같은 thread에서 같은 client_message_id로 재요청시 동일 결과 반환
# =========================
@router.post("/{thread_id}/messages", response_model=MessageOut)
def create_message(
    body: MessageCreate,
    thread: Thread = Depends(own_thread),
    db: Session = Depends(get_db),
):
    if not body.client_message_id:
        raise HTTPException(400, "client_message_id가 필요합니다. 멱등을 위해 필수입니다.")

    try:
        # 1) 이미 처리된 요청인지(assistant 응답까지 생성되었는지) 우선 확인
        existing_asst = (
            db.query(Message)
            .filter(
                Message.thread_id == thread.thread_id,
                Message.sender_type == "assistant",
                Message.response_to_client_message_id == body.client_message_id,
            )
            .order_by(Message.message_id.desc())
            .first()
        )
        if existing_asst:
            return existing_asst

        # 2) 사용자 메시지 존재 여부 확인(없으면 생성)
        user_msg = (
            db.query(Message)
            .filter(
                Message.thread_id == thread.thread_id,
                Message.sender_type == "user",
                Message.client_message_id == body.client_message_id,
            )
            .first()
        )
        if not user_msg:
            user_msg = Message(
                thread_id=thread.thread_id,
                sender_type="user",
                content=body.content,
                client_message_id=body.client_message_id,
            )
            db.add(user_msg)
            db.flush()  # message_id 확보

        # 3) LLM 호출 (sllm 연결 지점) —— 지금은 비워둠
        # text_chunks = []
        # async def _consume():
        #     async for delta in sllm.stream(body.content, thread=thread):  # 예: sllm.stream(...)
        #         text_chunks.append(delta)
        # anyio.run(_consume)
        # full_text = "".join(text_chunks)

        full_text = ""  # <-- sllm 연결 전까지는 빈 문자열 (또는 서버 내부에서 "준비중" 등 고정메시지 사용 가능)

        # 4) assistant 메시지 저장
        asst_msg = Message(
            thread_id=thread.thread_id,
            sender_type="assistant",
            content=full_text,
            parent_message_id=user_msg.message_id,
            response_to_client_message_id=body.client_message_id,
        )
        db.add(asst_msg)
        db.commit()
        db.refresh(asst_msg)
        return asst_msg

    except Exception as e:
        db.rollback()
        raise


# =========================
# WebSocket: 인증 + 소유권 검사 + 스트리밍 골격
# - 클라에서 {type:"user_message", content, client_message_id} 전송
# - 서버는 delta/최종본/상태 이벤트를 순서대로 보냄
# - 트랜잭션 롤백 보장
# =========================
@router.websocket("/ws/{thread_id}")
async def ws_chat(websocket: WebSocket, thread_id: int):
    await websocket.accept()

    # --- 1) 토큰 추출 ---
    auth_header = websocket.headers.get("authorization")
    token = None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        q = websocket.query_params.get("token")
        if q:
            token = q.replace("Bearer ", "").strip()
    if not token:
        await websocket.close(code=4401)  # Unauthorized
        return

    # --- 2) 토큰 검증 ---
    try:
        payload = AuthHandler().decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=4401)
        return

    # --- 3) 스레드 소유권 검사 ---
    db: Session = next(get_db())
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if not user:
            await websocket.close(code=4404)
            return
        assert_thread_ownership(db, thread_id, user.user_id)
    except HTTPException:
        # 소유권 실패
        await websocket.close(code=4403)  # Forbidden
        return
    finally:
        db.close()

    # --- 4) 메시지 루프 ---
    try:
        while True:
            data = await websocket.receive_json()
            mtype = data.get("type")

            if mtype == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if mtype == "user_message":
                content = data.get("content", "") or ""
                client_message_id = data.get("client_message_id")
                if not client_message_id:
                    await websocket.send_json({"type": "error", "message": "client_message_id is required"})
                    continue

                # 새로운 세션(요청 단위 트랜잭션)
                db = next(get_db())
                try:
                    # 멱등: 기존 assistant 응답 있으면 즉시 반환
                    existing_asst = (
                        db.query(Message)
                        .filter(
                            Message.thread_id == thread_id,
                            Message.sender_type == "assistant",
                            Message.response_to_client_message_id == client_message_id,
                        )
                        .order_by(Message.message_id.desc())
                        .first()
                    )
                    if existing_asst:
                        await websocket.send_json({
                            "type": "message",
                            "role": "assistant",
                            "content": existing_asst.content,
                            "client_message_id": client_message_id
                        })
                        continue

                    # 사용자 메시지 upsert
                    user_msg = (
                        db.query(Message)
                        .filter(
                            Message.thread_id == thread_id,
                            Message.sender_type == "user",
                            Message.client_message_id == client_message_id,
                        )
                        .first()
                    )
                    if not user_msg:
                        user_msg = Message(
                            thread_id=thread_id,
                            sender_type="user",
                            content=content,
                            client_message_id=client_message_id,
                        )
                        db.add(user_msg)
                        db.flush()

                    await websocket.send_json({"type": "status", "value": "stream_start", "client_message_id": client_message_id})

                    # ---- sllm 스트리밍 연결 지점 ----
                    # async for delta in sllm.stream(content, thread_id=thread_id):
                    #     await websocket.send_json({"type": "delta", "value": delta, "client_message_id": client_message_id})
                    # full_text = sllm.final_text()  # 또는 누적 방식으로 조립
                    full_text = ""  # sllm 연결 전까지는 빈 문자열

                    # assistant 저장
                    asst_msg = Message(
                        thread_id=thread_id,
                        sender_type="assistant",
                        content=full_text,
                        parent_message_id=user_msg.message_id,
                        response_to_client_message_id=client_message_id,
                    )
                    db.add(asst_msg)
                    db.commit()
                    db.refresh(asst_msg)

                    await websocket.send_json({
                        "type": "message",
                        "role": "assistant",
                        "content": asst_msg.content,
                        "client_message_id": client_message_id
                    })
                    await websocket.send_json({"type": "status", "value": "stream_end", "client_message_id": client_message_id})

                except Exception:
                    db.rollback()
                    await websocket.send_json({"type": "error", "message": "internal_error", "client_message_id": client_message_id})
                finally:
                    db.close()

            elif mtype == "cancel":
                # TODO: sllm 생성 태스크 취소 로직 연결
                await websocket.send_json({"type": "status", "value": "canceled"})

            elif mtype == "auth_update":
                new_token = data.get("token")
                try:
                    payload = AuthHandler().decode_token(new_token)
                    user_id = int(payload.get("sub"))
                    await websocket.send_json({"type": "status", "value": "auth_updated"})
                except Exception:
                    await websocket.send_json({"type": "error", "message": "auth_invalid"})

    except WebSocketDisconnect:
        # 연결 종료
        pass
