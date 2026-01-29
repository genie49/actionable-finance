#!/usr/bin/env python3
"""
Telegram Bot으로 메시지 전송
"""

import os
import sys
import argparse
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv가 필요합니다.")
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


def send_message(bot_token: str, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
    """텔레그램 봇으로 메시지 전송"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # 텔레그램 메시지 길이 제한 (4096자)
    max_length = 4096

    if len(text) <= max_length:
        chunks = [text]
    else:
        # 긴 메시지는 분할
        chunks = []
        while text:
            if len(text) <= max_length:
                chunks.append(text)
                break
            # 줄바꿈 기준으로 분할
            split_pos = text.rfind('\n', 0, max_length)
            if split_pos == -1:
                split_pos = max_length
            chunks.append(text[:split_pos])
            text = text[split_pos:].lstrip('\n')

    for i, chunk in enumerate(chunks):
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": parse_mode,
        }

        response = requests.post(url, json=payload)
        data = response.json()

        if not data.get("ok"):
            # Markdown 파싱 실패시 plain text로 재시도
            if "can't parse" in data.get("description", "").lower():
                payload["parse_mode"] = None
                response = requests.post(url, json=payload)
                data = response.json()

            if not data.get("ok"):
                print(f"Error: {data.get('description', 'Unknown error')}")
                return False

        if len(chunks) > 1:
            print(f"  전송 {i+1}/{len(chunks)}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Telegram Bot으로 메시지 전송")
    parser.add_argument("message", nargs="?", help="전송할 메시지 (없으면 stdin에서 읽음)")
    parser.add_argument("--file", "-f", type=str, help="전송할 파일 경로")
    parser.add_argument("--chat-id", type=str, help="Chat ID (기본: 환경변수)")
    args = parser.parse_args()

    project_root = find_project_root()
    load_dotenv(project_root / ".env")

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = args.chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN이 필요합니다.")
        sys.exit(1)

    if not chat_id:
        print("Error: TELEGRAM_CHAT_ID가 필요합니다.")
        print("먼저 scripts/get_chat_id.py를 실행하세요.")
        sys.exit(1)

    # 메시지 결정
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.message:
        text = args.message
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("Error: 전송할 메시지가 없습니다.")
        sys.exit(1)

    print(f"전송 중... ({len(text)}자)")
    if send_message(bot_token, chat_id, text):
        print("전송 완료!")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
