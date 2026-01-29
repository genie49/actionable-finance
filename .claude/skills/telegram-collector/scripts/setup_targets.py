#!/usr/bin/env python3
"""
Telegram 수집 대상 설정 헬퍼
사용자의 그룹/채널 목록을 가져와서 수집 대상을 선택하고 저장
"""

import asyncio
import json
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
    """프로젝트 루트 찾기 (.git 또는 .env 기준)"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_env():
    """환경변수 로드"""
    if load_dotenv:
        project_root = find_project_root()
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)


async def get_dialogs(client: TelegramClient) -> list[dict]:
    """사용자의 모든 대화 목록 가져오기"""
    dialogs = []

    async for dialog in client.iter_dialogs():
        entity = dialog.entity

        dialog_info = {
            "id": dialog.id,
            "name": dialog.name,
            "unread_count": dialog.unread_count,
        }

        if isinstance(entity, Channel):
            if entity.megagroup:
                dialog_info["type"] = "supergroup"
            elif entity.broadcast:
                dialog_info["type"] = "channel"
            else:
                dialog_info["type"] = "group"
            dialog_info["username"] = entity.username
            dialog_info["participants_count"] = getattr(entity, "participants_count", None)
        elif isinstance(entity, Chat):
            dialog_info["type"] = "group"
            dialog_info["username"] = None
        elif isinstance(entity, User):
            dialog_info["type"] = "user"
            dialog_info["username"] = entity.username
        else:
            dialog_info["type"] = "unknown"

        dialogs.append(dialog_info)

    return dialogs


def display_dialogs(dialogs: list[dict], filter_type: str | None = None):
    """대화 목록 표시"""
    filtered = dialogs
    if filter_type:
        filtered = [d for d in dialogs if d["type"] == filter_type]

    print(f"\n{'번호':<5} {'타입':<12} {'이름':<30} {'Username':<20} {'ID'}")
    print("-" * 90)

    for i, d in enumerate(filtered, 1):
        type_str = d["type"]
        name = d["name"][:28] if len(d["name"]) > 28 else d["name"]
        username = f"@{d['username']}" if d.get("username") else "-"
        print(f"{i:<5} {type_str:<12} {name:<30} {username:<20} {d['id']}")

    return filtered


def interactive_select(dialogs: list[dict]) -> list[dict]:
    """대화형으로 수집 대상 선택"""
    selected = []

    while True:
        print("\n" + "=" * 50)
        print("수집 대상 설정")
        print("=" * 50)
        print("1. 전체 목록 보기")
        print("2. 그룹/슈퍼그룹만 보기")
        print("3. 채널만 보기")
        print("4. 번호로 선택하기")
        print("5. ID로 직접 추가하기")
        print("6. 현재 선택 목록 보기")
        print("7. 저장하고 종료")
        print("0. 취소")

        choice = input("\n선택: ").strip()

        if choice == "1":
            display_dialogs(dialogs)
        elif choice == "2":
            filtered = [d for d in dialogs if d["type"] in ("group", "supergroup")]
            display_dialogs(filtered)
        elif choice == "3":
            filtered = [d for d in dialogs if d["type"] == "channel"]
            display_dialogs(filtered)
        elif choice == "4":
            print("\n먼저 목록을 선택하세요:")
            print("1. 그룹/슈퍼그룹")
            print("2. 채널")
            print("3. 전체")

            list_choice = input("선택: ").strip()
            if list_choice == "1":
                filtered = [d for d in dialogs if d["type"] in ("group", "supergroup")]
            elif list_choice == "2":
                filtered = [d for d in dialogs if d["type"] == "channel"]
            else:
                filtered = dialogs

            displayed = display_dialogs(filtered)

            print("\n추가할 번호를 입력하세요 (쉼표로 구분, 예: 1,3,5)")
            nums = input("번호: ").strip()

            try:
                indices = [int(n.strip()) - 1 for n in nums.split(",") if n.strip()]
                for idx in indices:
                    if 0 <= idx < len(displayed):
                        item = displayed[idx]
                        if item not in selected:
                            selected.append(item)
                            print(f"  추가됨: {item['name']}")
                        else:
                            print(f"  이미 선택됨: {item['name']}")
            except ValueError:
                print("잘못된 입력입니다.")

        elif choice == "5":
            print("\nID 또는 @username을 입력하세요:")
            identifier = input("입력: ").strip()

            # 기존 목록에서 찾기
            found = None
            for d in dialogs:
                if str(d["id"]) == identifier:
                    found = d
                    break
                if d.get("username") and f"@{d['username']}" == identifier:
                    found = d
                    break
                if d.get("username") == identifier.lstrip("@"):
                    found = d
                    break

            if found:
                if found not in selected:
                    selected.append(found)
                    print(f"추가됨: {found['name']}")
                else:
                    print(f"이미 선택됨: {found['name']}")
            else:
                # 직접 추가
                selected.append({
                    "id": identifier,
                    "name": identifier,
                    "type": "unknown",
                    "username": identifier.lstrip("@") if identifier.startswith("@") else None
                })
                print(f"직접 추가됨: {identifier}")

        elif choice == "6":
            if selected:
                print("\n현재 선택된 대상:")
                for i, s in enumerate(selected, 1):
                    print(f"  {i}. {s['name']} ({s['type']}) - {s['id']}")

                print("\n삭제할 번호 입력 (없으면 Enter):")
                del_num = input("삭제: ").strip()
                if del_num:
                    try:
                        idx = int(del_num) - 1
                        if 0 <= idx < len(selected):
                            removed = selected.pop(idx)
                            print(f"삭제됨: {removed['name']}")
                    except ValueError:
                        pass
            else:
                print("\n선택된 대상이 없습니다.")

        elif choice == "7":
            return selected

        elif choice == "0":
            return None

    return selected


def save_targets(targets: list[dict], output_path: Path):
    """선택된 대상 저장"""
    # 저장할 형식으로 변환
    save_data = {
        "targets": [
            {
                "id": t["id"],
                "name": t["name"],
                "type": t["type"],
                "username": t.get("username"),
                "enabled": True,
            }
            for t in targets
        ]
    }

    output_path.write_text(json.dumps(save_data, ensure_ascii=False, indent=2))
    print(f"\n저장 완료: {output_path}")


async def main():
    load_env()

    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    session_string = os.environ.get("TELEGRAM_SESSION_STRING")

    if not api_id or not api_hash:
        print("Error: TELEGRAM_API_ID, TELEGRAM_API_HASH 환경변수가 필요합니다.")
        exit(1)

    # StringSession 우선 사용
    if session_string:
        session = StringSession(session_string)
    else:
        session = os.environ.get("TELEGRAM_SESSION", "telegram_collector")

    client = TelegramClient(session, int(api_id), api_hash)

    project_root = find_project_root()
    output_path = project_root / "telegram-targets.json"

    async with client:
        if not await client.is_user_authorized():
            print("Error: 로그인이 필요합니다.")
            print("먼저 scripts/generate_session.py를 실행하여 세션을 생성하세요.")
            exit(1)

        print("대화 목록을 가져오는 중...")
        dialogs = await get_dialogs(client)
        print(f"총 {len(dialogs)}개의 대화를 찾았습니다.")

        selected = interactive_select(dialogs)

        if selected:
            save_targets(selected, output_path)
            print(f"\n{len(selected)}개의 수집 대상이 설정되었습니다.")
        else:
            print("\n취소되었습니다.")


if __name__ == "__main__":
    asyncio.run(main())
