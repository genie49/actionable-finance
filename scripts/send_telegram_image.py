#!/usr/bin/env python3
"""
Telegram Bot으로 이미지 전송
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


def send_photo(bot_token: str, chat_id: str, photo_path: str, caption: str = None) -> bool:
    """텔레그램 봇으로 이미지 전송"""
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

    photo_file = Path(photo_path)
    if not photo_file.exists():
        print(f"Error: 파일을 찾을 수 없음: {photo_path}")
        return False

    with open(photo_file, "rb") as f:
        files = {"photo": f}
        data = {"chat_id": chat_id}

        if caption:
            # 캡션 길이 제한 (1024자)
            if len(caption) > 1024:
                caption = caption[:1021] + "..."
            data["caption"] = caption
            data["parse_mode"] = "Markdown"

        response = requests.post(url, files=files, data=data)
        result = response.json()

        if not result.get("ok"):
            # Markdown 파싱 실패시 plain text로 재시도
            if caption and "can't parse" in result.get("description", "").lower():
                data.pop("parse_mode", None)
                f.seek(0)
                files = {"photo": f}
                response = requests.post(url, files=files, data=data)
                result = response.json()

            if not result.get("ok"):
                print(f"Error: {result.get('description', 'Unknown error')}")
                return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Telegram Bot으로 이미지 전송")
    parser.add_argument("image", help="전송할 이미지 파일 경로")
    parser.add_argument("--caption", "-c", type=str, help="이미지 캡션")
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

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: 파일을 찾을 수 없음: {args.image}")
        sys.exit(1)

    print(f"전송 중... ({image_path.name})")
    if send_photo(bot_token, chat_id, str(image_path), args.caption):
        print("전송 완료!")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
