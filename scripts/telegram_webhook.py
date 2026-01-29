#!/usr/bin/env python3
"""
Telegram Bot Webhook Server

사용법:
1. ngrok으로 터널 열기: ngrok http 8000
2. 서버 실행: python scripts/telegram_webhook.py --webhook-url https://xxxx.ngrok.io/webhook
3. 또는 로컬 테스트: python scripts/telegram_webhook.py --local

환경변수:
- TELEGRAM_BOT_TOKEN: 봇 토큰
- TELEGRAM_CHAT_ID: 기본 채팅 ID (선택)
"""

import os
import sys
import json
import argparse
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Awaitable

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: pip install python-dotenv")
    sys.exit(1)

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("Error: pip install fastapi uvicorn")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("Error: pip install httpx")
    sys.exit(1)


def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()


# 프로젝트 루트 및 환경변수 로드
PROJECT_ROOT = find_project_root()
load_dotenv(PROJECT_ROOT / ".env")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN이 필요합니다.")
    sys.exit(1)

# FastAPI 앱
app = FastAPI(title="Telegram Webhook Bot")

# 메시지 핸들러 저장소
MessageHandler = Callable[[dict], Awaitable[Optional[str]]]
_message_handlers: list[MessageHandler] = []


def on_message(handler: MessageHandler):
    """메시지 핸들러 데코레이터"""
    _message_handlers.append(handler)
    return handler


async def send_message(chat_id: int, text: str, parse_mode: str = "Markdown") -> bool:
    """텔레그램으로 메시지 전송"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    async with httpx.AsyncClient() as client:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        response = await client.post(url, json=payload)
        data = response.json()

        if not data.get("ok"):
            # Markdown 파싱 실패시 plain text로 재시도
            if "can't parse" in data.get("description", "").lower():
                payload["parse_mode"] = None
                response = await client.post(url, json=payload)
                data = response.json()

        return data.get("ok", False)


async def set_webhook(webhook_url: str) -> bool:
    """텔레그램에 Webhook URL 등록"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={"url": webhook_url})
        data = response.json()

        if data.get("ok"):
            print(f"Webhook 설정 완료: {webhook_url}")
            return True
        else:
            print(f"Webhook 설정 실패: {data.get('description')}")
            return False


async def delete_webhook() -> bool:
    """Webhook 삭제 (polling 모드로 전환시 필요)"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"

    async with httpx.AsyncClient() as client:
        response = await client.post(url)
        data = response.json()
        return data.get("ok", False)


@app.post("/webhook")
async def webhook_handler(request: Request):
    """텔레그램 Webhook 엔드포인트"""
    try:
        update = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # 메시지 추출
    message = update.get("message")
    if not message:
        return JSONResponse({"ok": True})

    chat = message.get("chat", {})
    from_user = message.get("from", {})
    text = message.get("text", "")

    # 메시지 정보 구성
    msg_info = {
        "update_id": update.get("update_id"),
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

    # 등록된 핸들러 실행
    for handler in _message_handlers:
        try:
            reply = await handler(msg_info)
            if reply:
                await send_message(chat.get("id"), reply)
        except Exception as e:
            print(f"Handler error: {e}")

    return JSONResponse({"ok": True})


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok", "bot_token_set": bool(BOT_TOKEN)}


# ===== 기본 메시지 핸들러 예시 =====

@on_message
async def echo_handler(msg: dict) -> Optional[str]:
    """에코 핸들러 - 받은 메시지를 그대로 반환"""
    text = msg.get("text", "")

    # /start 명령어
    if text == "/start":
        return "안녕하세요! 무엇을 도와드릴까요?"

    # /help 명령어
    if text == "/help":
        return """사용 가능한 명령어:
/start - 시작
/help - 도움말
/echo <메시지> - 에코"""

    # /echo 명령어
    if text.startswith("/echo "):
        return text[6:]

    # 일반 메시지는 에코
    if text and not text.startswith("/"):
        return f"받은 메시지: {text}"

    return None


# ===== 커스텀 핸들러 추가 예시 =====
# @on_message
# async def custom_handler(msg: dict) -> Optional[str]:
#     text = msg.get("text", "")
#     if "안녕" in text:
#         return "안녕하세요!"
#     return None


def main():
    parser = argparse.ArgumentParser(description="Telegram Webhook Bot Server")
    parser.add_argument("--host", default="0.0.0.0", help="호스트 (기본: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="포트 (기본: 8000)")
    parser.add_argument("--webhook-url", help="Webhook URL (예: https://xxxx.ngrok.io/webhook)")
    parser.add_argument("--local", action="store_true", help="로컬 테스트 모드 (webhook 설정 안함)")
    parser.add_argument("--delete-webhook", action="store_true", help="Webhook 삭제 후 종료")
    args = parser.parse_args()

    # Webhook 삭제 모드
    if args.delete_webhook:
        asyncio.run(delete_webhook())
        print("Webhook 삭제 완료")
        return

    # Webhook URL 설정만 하고 종료
    if args.webhook_url:
        webhook_url = args.webhook_url
        if not webhook_url.endswith("/webhook"):
            webhook_url = webhook_url.rstrip("/") + "/webhook"
        asyncio.run(set_webhook(webhook_url))
        return  # 등록만 하고 종료

    print(f"\nBot 서버 시작: http://{args.host}:{args.port}")
    print("Webhook endpoint: /webhook")
    print("Health check: /health")
    print("\nCtrl+C로 종료\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
