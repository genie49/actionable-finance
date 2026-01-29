#!/usr/bin/env python3
"""
Telegram StringSession 생성기
한 번 실행하여 세션 문자열을 생성하고 .env에 저장
"""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv, set_key
except ImportError:
    print("Error: python-dotenv가 설치되어 있지 않습니다.")
    print("설치: pip install python-dotenv")
    sys.exit(1)

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
except ImportError:
    print("Error: telethon이 설치되어 있지 않습니다.")
    print("설치: pip install telethon")
    sys.exit(1)


def find_project_root() -> Path:
    """프로젝트 루트 찾기"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()


async def main():
    project_root = find_project_root()
    env_path = project_root / ".env"

    # .env 로드
    if env_path.exists():
        load_dotenv(env_path)

    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        print("Error: .env 파일에 TELEGRAM_API_ID와 TELEGRAM_API_HASH가 필요합니다.")
        print(f"경로: {env_path}")
        sys.exit(1)

    print("=" * 50)
    print("Telegram StringSession 생성기")
    print("=" * 50)
    print()
    print("이 스크립트는 한 번만 실행하면 됩니다.")
    print("생성된 세션 문자열은 .env 파일에 자동 저장됩니다.")
    print()

    # StringSession으로 클라이언트 생성
    client = TelegramClient(StringSession(), int(api_id), api_hash)

    await client.start()

    # 세션 문자열 추출
    session_string = client.session.save()

    print()
    print("=" * 50)
    print("세션 생성 완료!")
    print("=" * 50)
    print()

    # .env 파일에 저장
    if env_path.exists():
        set_key(str(env_path), "TELEGRAM_SESSION_STRING", session_string)
        print(f"✓ .env 파일에 저장됨: {env_path}")
    else:
        print("세션 문자열 (이 값을 .env에 추가하세요):")
        print()
        print(f"TELEGRAM_SESSION_STRING={session_string}")

    print()
    print("이제 메시지 수집 스크립트를 자동으로 실행할 수 있습니다.")

    await client.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
