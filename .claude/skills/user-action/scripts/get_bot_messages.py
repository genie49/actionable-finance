#!/usr/bin/env python3
"""
Telegram Bot에 온 메시지 조회 + 대화 히스토리
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv가 필요합니다.")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests가 필요합니다.")
    sys.exit(1)

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
except ImportError:
    print("Error: telethon이 필요합니다.")
    sys.exit(1)


def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_updates(bot_token: str, limit: int = 10) -> list[dict]:
    """Bot API로 새 메시지 조회"""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {"limit": limit}

    response = requests.get(url, params=params)
    data = response.json()

    if not data.get("ok"):
        print(f"Error: {data.get('description', 'Unknown error')}")
        return []

    messages = []
    for update in data.get("result", []):
        msg = update.get("message", {})
        if not msg:
            continue

        chat = msg.get("chat", {})
        from_user = msg.get("from", {})

        messages.append({
            "update_id": update.get("update_id"),
            "message_id": msg.get("message_id"),
            "date": datetime.fromtimestamp(msg.get("date", 0)).isoformat(),
            "chat_id": chat.get("id"),
            "chat_type": chat.get("type"),
            "from_id": from_user.get("id"),
            "from_name": f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip(),
            "from_username": from_user.get("username"),
            "text": msg.get("text", ""),
        })

    return messages


def mark_as_read(bot_token: str, last_update_id: int):
    """메시지를 읽음 처리 (다음 조회시 제외)"""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    requests.get(url, params={"offset": last_update_id + 1})


async def get_chat_history(limit: int = 8) -> list[dict]:
    """Telethon으로 봇과의 대화 히스토리 조회"""
    project_root = find_project_root()
    load_dotenv(project_root / ".env")

    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    session_string = os.environ.get("TELEGRAM_SESSION_STRING")

    if not all([api_id, api_hash, session_string]):
        return []

    session = StringSession(session_string)
    client = TelegramClient(session, int(api_id), api_hash)

    messages = []
    async with client:
        # dialogs에서 봇 entity 찾기
        target_entity = None
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            if getattr(entity, 'bot', False):
                target_entity = entity
                break

        if not target_entity:
            return []

        async for msg in client.iter_messages(target_entity, limit=limit):
            sender = await msg.get_sender()
            sender_name = "Unknown"
            is_bot = False

            if sender:
                sender_name = f"{getattr(sender, 'first_name', '') or ''} {getattr(sender, 'last_name', '') or ''}".strip()
                is_bot = getattr(sender, 'bot', False)

            messages.append({
                "message_id": msg.id,
                "date": msg.date.isoformat(),
                "sender_name": sender_name or "Unknown",
                "is_bot": is_bot,
                "text": msg.text or "",
            })

    # 오래된 순으로 정렬
    messages.reverse()
    return messages


def main():
    parser = argparse.ArgumentParser(description="Telegram Bot 메시지 조회")
    parser.add_argument("--limit", "-n", type=int, default=10, help="조회할 업데이트 수")
    parser.add_argument("--history", type=int, default=8, help="불러올 이전 메시지 수")
    parser.add_argument("--mark-read", action="store_true", help="조회 후 읽음 처리")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    project_root = find_project_root()
    load_dotenv(project_root / ".env")

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN이 필요합니다.")
        sys.exit(1)

    # 새 메시지 확인
    updates = get_updates(bot_token, limit=args.limit)

    if not updates:
        print("새 메시지가 없습니다.")
        return

    # 봇과의 대화 히스토리 조회
    history = asyncio.run(get_chat_history(limit=args.history))

    if args.json:
        output = {
            "new_updates": updates,
            "chat_history": history,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"=== 대화 히스토리 (최근 {len(history)}개) ===\n")
        for msg in history:
            role = "[봇]" if msg["is_bot"] else "[사용자]"
            date = datetime.fromisoformat(msg["date"]).strftime("%H:%M")
            print(f"{role} [{date}] {msg['sender_name']}: {msg['text']}")

        print(f"\n=== 새 메시지 ({len(updates)}개) ===\n")
        for msg in updates:
            print(f"[{msg['date']}] {msg['from_name']}: {msg['text']}")

    if args.mark_read and updates:
        last_id = max(m["update_id"] for m in updates)
        mark_as_read(bot_token, last_id)
        print("\n(메시지 읽음 처리 완료)")


if __name__ == "__main__":
    main()
