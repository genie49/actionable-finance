#!/usr/bin/env python3
"""
Telegram Bot과의 대화 히스토리 조회 (Telethon 사용)
Webhook 환경에서 최근 메시지를 조회할 때 사용
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


async def get_chat_history(limit: int = 10) -> list[dict]:
    """Telethon으로 봇과의 대화 히스토리 조회"""
    project_root = find_project_root()
    load_dotenv(project_root / ".env")

    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    session_string = os.environ.get("TELEGRAM_SESSION_STRING")
    bot_username = os.environ.get("TELEGRAM_BOT_USERNAME")

    if not all([api_id, api_hash, session_string]):
        print("Error: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION_STRING이 필요합니다.")
        return []

    session = StringSession(session_string)
    client = TelegramClient(session, int(api_id), api_hash)

    messages = []
    async with client:
        # 봇 entity 찾기
        target_entity = None

        # 환경변수에 봇 username이 있으면 직접 사용
        if bot_username:
            try:
                target_entity = await client.get_entity(bot_username)
            except Exception:
                pass

        # 없으면 dialogs에서 찾기
        if not target_entity:
            async for dialog in client.iter_dialogs():
                entity = dialog.entity
                if getattr(entity, 'bot', False):
                    target_entity = entity
                    break

        if not target_entity:
            print("Error: 봇을 찾을 수 없습니다.")
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
    parser = argparse.ArgumentParser(description="Telegram Bot 대화 히스토리 조회")
    parser.add_argument("--limit", "-n", type=int, default=10, help="조회할 메시지 수 (기본: 10)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    messages = asyncio.run(get_chat_history(limit=args.limit))

    if not messages:
        print("메시지가 없습니다.")
        return

    if args.json:
        print(json.dumps(messages, ensure_ascii=False, indent=2))
    else:
        print(f"=== 최근 대화 ({len(messages)}개) ===\n")
        for msg in messages:
            role = "[봇]" if msg["is_bot"] else "[사용자]"
            date = datetime.fromisoformat(msg["date"]).strftime("%m/%d %H:%M")
            print(f"{role} [{date}] {msg['text']}")


if __name__ == "__main__":
    main()
