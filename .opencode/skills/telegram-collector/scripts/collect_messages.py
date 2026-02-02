#!/usr/bin/env python3
"""
Telegram 메시지 수집기 - Telethon 기반
지정된 그룹/채널에서 최근 24시간 메시지를 수집하여 Markdown으로 저장
"""

import asyncio
import argparse
import os
import json
from datetime import datetime, timedelta, timezone
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
    """프로젝트 루트 찾기 (.git 또는 .env 기준)"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_config() -> dict:
    """환경변수, .env, 또는 config 파일에서 설정 로드"""
    project_root = find_project_root()

    # .env 파일 로드
    if load_dotenv:
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)

    config = {
        "api_id": os.environ.get("TELEGRAM_API_ID"),
        "api_hash": os.environ.get("TELEGRAM_API_HASH"),
        "session_string": os.environ.get("TELEGRAM_SESSION_STRING"),
        "session_name": os.environ.get("TELEGRAM_SESSION", "telegram_collector"),
        "project_root": project_root,
    }

    # config.json 파일이 있으면 로드
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            file_config = json.load(f)
            for key, value in file_config.items():
                if not config.get(key):
                    config[key] = value

    return config


def load_targets(project_root: Path) -> list[str]:
    """telegram-targets.json에서 활성화된 대상 로드"""
    targets_path = project_root / "telegram-targets.json"
    if not targets_path.exists():
        return []

    with open(targets_path) as f:
        data = json.load(f)

    targets = []
    for t in data.get("targets", []):
        if t.get("enabled", True):
            # username이 있으면 우선 사용, 없으면 ID
            if t.get("username"):
                targets.append(f"@{t['username']}")
            else:
                targets.append(str(t["id"]))

    return targets


async def get_entity_info(client: TelegramClient, entity) -> dict:
    """엔티티(그룹/채널/사용자) 정보 추출"""
    if isinstance(entity, User):
        return {
            "type": "user",
            "id": entity.id,
            "name": f"{entity.first_name or ''} {entity.last_name or ''}".strip(),
            "username": entity.username,
        }
    elif isinstance(entity, (Channel, Chat)):
        return {
            "type": "channel" if isinstance(entity, Channel) else "group",
            "id": entity.id,
            "name": entity.title,
            "username": getattr(entity, "username", None),
        }
    return {"type": "unknown", "id": getattr(entity, "id", None)}


async def collect_messages(
    client: TelegramClient,
    chat_identifier: str,
    hours: int = 24,
    user_ids: list[int] | None = None,
) -> list[dict]:
    """
    지정된 채팅에서 메시지 수집

    Args:
        client: Telethon 클라이언트
        chat_identifier: 채팅 ID, username, 또는 invite link
        hours: 수집할 시간 범위 (기본 24시간)
        user_ids: 필터링할 사용자 ID 목록 (None이면 전체)

    Returns:
        수집된 메시지 목록
    """
    messages = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

    try:
        entity = await client.get_entity(chat_identifier)
        chat_info = await get_entity_info(client, entity)
    except Exception as e:
        print(f"Error: 채팅을 찾을 수 없습니다 - {chat_identifier}: {e}")
        return messages

    print(f"수집 중: {chat_info['name']} ({chat_info['type']})")

    async for message in client.iter_messages(entity):
        if message.date < cutoff_time:
            break

        # 사용자 필터링
        if user_ids and message.sender_id not in user_ids:
            continue

        # 메시지 정보 추출
        sender = await message.get_sender()
        sender_info = await get_entity_info(client, sender) if sender else {"name": "Unknown"}

        msg_data = {
            "id": message.id,
            "date": message.date.isoformat(),
            "sender_id": message.sender_id,
            "sender_name": sender_info.get("name", "Unknown"),
            "sender_username": sender_info.get("username"),
            "text": message.text or "",
            "has_media": message.media is not None,
            "reply_to": message.reply_to_msg_id,
        }
        messages.append(msg_data)

    print(f"  수집 완료: {len(messages)}개 메시지")
    return messages


def format_markdown(messages: list[dict], chat_name: str, hours: int) -> str:
    """메시지를 Markdown 형식으로 포맷팅"""
    now = datetime.now()

    lines = [
        f"# {chat_name} 메시지 수집",
        f"",
        f"- 수집 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 기간: 최근 {hours}시간",
        f"- 총 메시지: {len(messages)}개",
        f"",
        "---",
        "",
    ]

    # 시간순 정렬 (오래된 것 먼저)
    sorted_messages = sorted(messages, key=lambda x: x["date"])

    current_date = None
    for msg in sorted_messages:
        msg_date = datetime.fromisoformat(msg["date"])
        date_str = msg_date.strftime("%Y-%m-%d")

        # 날짜 구분
        if date_str != current_date:
            current_date = date_str
            lines.append(f"## {date_str}")
            lines.append("")

        # 메시지 포맷
        time_str = msg_date.strftime("%H:%M")
        sender = msg["sender_name"]
        if msg["sender_username"]:
            sender = f"{sender} (@{msg['sender_username']})"

        text = msg["text"] if msg["text"] else "[미디어]" if msg["has_media"] else "[빈 메시지]"

        # 멀티라인 텍스트 처리
        if "\n" in text:
            lines.append(f"**[{time_str}] {sender}:**")
            lines.append(f"> {text.replace(chr(10), chr(10) + '> ')}")
        else:
            lines.append(f"**[{time_str}] {sender}:** {text}")

        lines.append("")

    return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(description="Telegram 메시지 수집기")
    parser.add_argument(
        "chats",
        nargs="*",
        help="수집할 채팅 (미지정시 telegram-targets.json 사용)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="수집할 시간 범위 (기본: 24)",
    )
    parser.add_argument(
        "--users",
        type=int,
        nargs="*",
        help="필터링할 사용자 ID 목록",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="출력 파일 경로 (기본: collected_messages/YYYY-MM-DD.md)",
    )
    parser.add_argument(
        "--api-id",
        type=str,
        help="Telegram API ID (환경변수 TELEGRAM_API_ID로도 설정 가능)",
    )
    parser.add_argument(
        "--api-hash",
        type=str,
        help="Telegram API Hash (환경변수 TELEGRAM_API_HASH로도 설정 가능)",
    )

    args = parser.parse_args()

    # 설정 로드
    config = load_config()
    api_id = args.api_id or config.get("api_id")
    api_hash = args.api_hash or config.get("api_hash")

    if not api_id or not api_hash:
        print("Error: Telegram API 인증 정보가 필요합니다.")
        print("환경변수 설정: TELEGRAM_API_ID, TELEGRAM_API_HASH")
        print("또는 --api-id, --api-hash 옵션 사용")
        print("\nAPI 키는 https://my.telegram.org 에서 발급받을 수 있습니다.")
        exit(1)

    # 수집 대상 결정
    chats = args.chats
    if not chats:
        chats = load_targets(config["project_root"])
        if not chats:
            print("Error: 수집 대상이 없습니다.")
            print("사용법: python collect_messages.py @channel_name")
            print("또는: python setup_targets.py 로 대상 설정")
            exit(1)
        print(f"telegram-targets.json에서 {len(chats)}개 대상 로드")

    # 클라이언트 생성 및 연결
    session_string = config.get("session_string")
    if session_string:
        session = StringSession(session_string)
    else:
        session = config["session_name"]

    client = TelegramClient(session, int(api_id), api_hash)

    async with client:
        if not await client.is_user_authorized():
            print("Error: 로그인이 필요합니다.")
            print("먼저 scripts/generate_session.py를 실행하여 세션을 생성하세요.")
            exit(1)

        all_messages = []
        chat_names = []

        for chat in chats:
            messages = await collect_messages(
                client,
                chat,
                hours=args.hours,
                user_ids=args.users,
            )
            if messages:
                all_messages.extend(messages)
                # 채팅 이름 추출
                try:
                    entity = await client.get_entity(chat)
                    chat_info = await get_entity_info(client, entity)
                    chat_names.append(chat_info["name"])
                except:
                    chat_names.append(chat)

        if not all_messages:
            print("수집된 메시지가 없습니다.")
            return

        # Markdown 생성
        chat_title = ", ".join(chat_names) if len(chat_names) <= 3 else f"{len(chat_names)}개 채팅"
        markdown = format_markdown(all_messages, chat_title, args.hours)

        # 출력 경로 결정
        if args.output:
            output_path = Path(args.output)
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            output_path = config["project_root"] / "collected_messages" / f"{today}.md"

        # 파일 저장
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")

        print(f"\n저장 완료: {output_path}")
        print(f"총 {len(all_messages)}개 메시지 수집")


if __name__ == "__main__":
    asyncio.run(main())
