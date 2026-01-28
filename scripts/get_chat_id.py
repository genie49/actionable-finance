#!/usr/bin/env python3
"""
Telegram Bot Chat ID 확인
봇에 /start 메시지 보낸 후 실행
"""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv, set_key
except ImportError:
    print("Error: python-dotenv가 필요합니다.")
    print("설치: pip install python-dotenv")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests가 필요합니다.")
    print("설치: pip install requests")
    sys.exit(1)


def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()


def main():
    project_root = find_project_root()
    env_path = project_root / ".env"
    load_dotenv(env_path)

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        sys.exit(1)

    print("봇에 메시지를 보낸 사용자 목록을 확인합니다...")
    print("(먼저 @actionable_finance_bot 에 /start 메시지를 보내세요)\n")

    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url)
    data = response.json()

    if not data.get("ok"):
        print(f"Error: {data.get('description', 'Unknown error')}")
        sys.exit(1)

    results = data.get("result", [])
    if not results:
        print("아직 봇에 메시지를 보낸 사용자가 없습니다.")
        print("@actionable_finance_bot 에서 /start 를 보내세요.")
        sys.exit(0)

    seen_chats = {}
    for update in results:
        msg = update.get("message", {})
        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        if chat_id and chat_id not in seen_chats:
            seen_chats[chat_id] = {
                "id": chat_id,
                "type": chat.get("type"),
                "name": chat.get("first_name", "") + " " + chat.get("last_name", ""),
                "username": chat.get("username"),
            }

    print(f"{'Chat ID':<15} {'Type':<10} {'Name':<20} {'Username'}")
    print("-" * 60)

    for chat_id, info in seen_chats.items():
        username = f"@{info['username']}" if info['username'] else "-"
        print(f"{info['id']:<15} {info['type']:<10} {info['name'].strip():<20} {username}")

    # 첫 번째 chat_id를 .env에 저장할지 묻기
    if len(seen_chats) == 1:
        chat_id = list(seen_chats.keys())[0]
        print(f"\n이 Chat ID를 .env에 저장합니다: {chat_id}")
        set_key(str(env_path), "TELEGRAM_CHAT_ID", str(chat_id))
        print("저장 완료!")
    elif len(seen_chats) > 1:
        print("\n여러 사용자가 있습니다. 원하는 Chat ID를 .env의 TELEGRAM_CHAT_ID에 직접 입력하세요.")


if __name__ == "__main__":
    main()
