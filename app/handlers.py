"""웹훅 핸들러"""

import asyncio
from datetime import datetime
from typing import Optional, Callable, Awaitable

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.config import PROJECT_ROOT, WEBHOOK_SECRET
from app.telegram import send_message, send_chat_action

# 라우터
router = APIRouter(tags=["webhook"])

# 메시지 핸들러 저장소
MessageHandler = Callable[[dict], Awaitable[Optional[str]]]
_message_handlers: list[MessageHandler] = []

# 중복 처리 방지용
_processed_updates: set[int] = set()
_MAX_PROCESSED_UPDATES = 1000


def on_message(handler: MessageHandler):
    """메시지 핸들러 데코레이터"""
    _message_handlers.append(handler)
    return handler


async def process_message(msg_info: dict):
    """백그라운드에서 메시지 처리"""
    chat_id = msg_info.get("chat_id")

    # 타이핑 표시
    await send_chat_action(chat_id, "typing")

    # 등록된 핸들러 실행
    for handler in _message_handlers:
        try:
            reply = await handler(msg_info)
            if reply:
                await send_message(chat_id, reply)
        except Exception as e:
            print(f"Handler error: {e}")


@router.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """텔레그램 Webhook 엔드포인트"""
    # Secret token 검증
    if WEBHOOK_SECRET:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if token != WEBHOOK_SECRET:
            print(f"[보안] 잘못된 secret token: {token}")
            raise HTTPException(status_code=403, detail="Forbidden")

    try:
        update = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # 중복 처리 방지
    update_id = update.get("update_id")
    if update_id in _processed_updates:
        print(f"[중복] update_id={update_id} 이미 처리됨, 스킵")
        return JSONResponse({"ok": True})

    # 처리 완료 표시
    _processed_updates.add(update_id)
    if len(_processed_updates) > _MAX_PROCESSED_UPDATES:
        to_remove = list(_processed_updates)[:_MAX_PROCESSED_UPDATES // 2]
        for item in to_remove:
            _processed_updates.discard(item)

    # 메시지 추출
    message = update.get("message")
    if not message:
        return JSONResponse({"ok": True})

    chat = message.get("chat", {})
    from_user = message.get("from", {})
    text = message.get("text", "")

    # 메시지 정보 구성
    msg_info = {
        "update_id": update_id,
        "message_id": message.get("message_id"),
        "date": datetime.fromtimestamp(message.get("date", 0)).isoformat(),
        "chat_id": chat.get("id"),
        "chat_type": chat.get("type"),
        "from_id": from_user.get("id"),
        "from_name": f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip(),
        "from_username": from_user.get("username"),
        "text": text,
    }

    # 콘솔 로그
    print(f"\n[{msg_info['date']}] {msg_info['from_name']}: {text}")

    # 즉시 타이핑 표시
    chat_id = chat.get("id")
    print(f"[webhook] 타이핑 표시 시도: chat_id={chat_id}")
    await send_chat_action(chat_id, "typing")

    # 백그라운드에서 처리
    background_tasks.add_task(process_message, msg_info)

    return JSONResponse({"ok": True})


# ===== 타이핑 유지 =====

async def keep_typing(chat_id: int, stop_event: asyncio.Event):
    """OpenCode 실행 중 타이핑 표시 유지 (4초마다)"""
    while not stop_event.is_set():
        await send_chat_action(chat_id, "typing")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=4.0)
        except asyncio.TimeoutError:
            pass


# ===== OpenCode 핸들러 =====

@on_message
async def opencode_handler(msg: dict) -> Optional[str]:
    """OpenCode로 /user-action 실행"""
    text = msg.get("text", "")
    chat_id = msg.get("chat_id")

    # 빈 메시지 무시
    if not text:
        return None

    # /start, /help는 기본 응답
    if text == "/start":
        return "안녕하세요! 메시지를 보내주시면 AI가 답변해드립니다."

    if text == "/help":
        return "메시지를 보내주시면 AI가 분석하여 답변해드립니다."

    # 일반 메시지 → OpenCode 실행
    print(f"\n>>> OpenCode 실행: /user-action")

    # 타이핑 표시 시작
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(chat_id, stop_typing))

    try:
        process = await asyncio.create_subprocess_exec(
            "opencode", "run", "/user-action", "-m", "zai-coding-plan/glm-4.7",
            cwd=str(PROJECT_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=300.0  # 5분 타임아웃
        )

        if process.returncode == 0:
            print(f">>> OpenCode 완료")
        else:
            print(f">>> OpenCode 에러: {stderr.decode()}")

    except asyncio.TimeoutError:
        print(">>> OpenCode 타임아웃")
    except Exception as e:
        print(f">>> OpenCode 실행 실패: {e}")
    finally:
        # 타이핑 표시 중지
        stop_typing.set()
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass

    # OpenCode가 직접 send_telegram.py로 응답하므로 여기선 None 반환
    return None
