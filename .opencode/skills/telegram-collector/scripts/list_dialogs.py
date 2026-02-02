#!/usr/bin/env python3
"""
Telegram 대화 목록 조회
사용자의 모든 그룹/채널/DM 목록을 출력
"""

import asyncio
import argparse
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.tl.types import User, Channel, Chat
except ImportError:
    print("Error: telethon이 설치되어 있지 않습니다.")
    print("설치: pip install telethon")
    exit(1)


def find_project_root() -> Path:
    """프로젝트 루트 찾기"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_config() -> dict:
    """설정 로드"""
    project_root = find_project_root()

    if load_dotenv:
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)

    return {
        "api_id": os.environ.get("TELEGRAM_API_ID"),
        "api_hash": os.environ.get("TELEGRAM_API_HASH"),
        "session_string": os.environ.get("TELEGRAM_SESSION_STRING"),
    }


async def list_dialogs(client: TelegramClient, filter_type: str | None = None):
    """대화 목록 출력"""
    print(f"\n{'번호':<4} {'타입':<12} {'이름':<35} {'Username':<25} {'ID'}")
    print("-" * 100)

    i = 1
    async for dialog in client.iter_dialogs():
        entity = dialog.entity

        if isinstance(entity, Channel):
            if entity.megagroup:
                dtype = "supergroup"
            elif entity.broadcast:
                dtype = "channel"
            else:
                dtype = "group"
            username = f"@{entity.username}" if entity.username else "-"
        elif isinstance(entity, Chat):
            dtype = "group"
            username = "-"
        elif isinstance(entity, User):
            dtype = "user"
            username = f"@{entity.username}" if entity.username else "-"
        else:
            dtype = "unknown"
            username = "-"

        # 필터링
        if filter_type:
            if filter_type == "group" and dtype not in ("group", "supergroup"):
                continue
            elif filter_type == "channel" and dtype != "channel":
                continue
            elif filter_type == "user" and dtype != "user":
                continue

        name = dialog.name[:33] if len(dialog.name) > 33 else dialog.name
        print(f"{i:<4} {dtype:<12} {name:<35} {username:<25} {dialog.id}")
        i += 1


async def main():
    parser = argparse.ArgumentParser(description="Telegram 대화 목록 조회")
    parser.add_argument(
        "--type", "-t",
        choices=["all", "group", "channel", "user"],
        default="all",
        help="필터링할 대화 유형 (기본: all)",
    )

    args = parser.parse_args()

    config = load_config()

    if not config["api_id"] or not config["api_hash"]:
        print("Error: TELEGRAM_API_ID, TELEGRAM_API_HASH가 필요합니다.")
        exit(1)

    if not config["session_string"]:
        print("Error: TELEGRAM_SESSION_STRING이 필요합니다.")
        print("먼저 scripts/generate_session.py를 실행하세요.")
        exit(1)

    client = TelegramClient(
        StringSession(config["session_string"]),
        int(config["api_id"]),
        config["api_hash"],
    )

    async with client:
        filter_type = None if args.type == "all" else args.type
        await list_dialogs(client, filter_type)


if __name__ == "__main__":
    asyncio.run(main())
