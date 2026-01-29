#!/usr/bin/env python3
"""업비트 주문 취소 스크립트"""

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

import pyupbit


def find_project_root() -> Path:
    """프로젝트 루트 찾기 (.git 또는 .env 기준)"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_env():
    """프로젝트 루트의 .env 파일 로드"""
    if load_dotenv:
        project_root = find_project_root()
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)


def get_upbit_client():
    """업비트 클라이언트 생성"""
    load_env()
    access_key = os.getenv("UPBIT_ACCESS_KEY")
    secret_key = os.getenv("UPBIT_SECRET_KEY")

    if not access_key or not secret_key:
        print("Error: UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY 환경변수를 설정해주세요.", file=sys.stderr)
        sys.exit(1)

    return pyupbit.Upbit(access_key, secret_key)


def cancel_order(uuid: str) -> None:
    """주문 취소"""
    upbit = get_upbit_client()

    try:
        result = upbit.cancel_order(uuid)
    except Exception as e:
        print(f"Error: 주문 취소 실패 - {e}", file=sys.stderr)
        sys.exit(1)

    if not result:
        print("Error: 주문 취소 응답 없음", file=sys.stderr)
        sys.exit(1)

    if "error" in result:
        error_msg = result["error"].get("message", "알 수 없는 오류")
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)

    print("✅ 주문 취소 완료")
    print(f"   주문번호: {result.get('uuid', uuid)}")
    print(f"   마켓: {result.get('market', 'N/A')}")
    print(f"   주문타입: {result.get('side', 'N/A')}")
    print(f"   상태: {result.get('state', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(description="업비트 주문 취소")
    parser.add_argument("uuid", help="취소할 주문의 UUID")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        upbit = get_upbit_client()
        result = upbit.cancel_order(args.uuid)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        cancel_order(args.uuid)


if __name__ == "__main__":
    main()
