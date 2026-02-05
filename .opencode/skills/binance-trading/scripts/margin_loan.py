#!/usr/bin/env python3
"""바이낸스 마진 대출/상환 스크립트"""

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from binance.client import Client
from binance.exceptions import BinanceAPIException


def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_env():
    if load_dotenv:
        project_root = find_project_root()
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)


def format_number(num: float, decimals: int = 8) -> str:
    if num >= 1:
        return f"{num:,.{min(decimals, 2)}f}"
    return f"{num:.{decimals}f}".rstrip("0").rstrip(".")


def get_binance_client() -> Client:
    load_env()
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")

    if not api_key or not secret_key:
        print("Error: BINANCE_API_KEY, BINANCE_SECRET_KEY 환경변수를 설정해주세요.", file=sys.stderr)
        sys.exit(1)

    return Client(api_key, secret_key)


def margin_borrow(asset: str, amount: float) -> None:
    """마진 대출"""
    client = get_binance_client()
    asset = asset.upper()

    try:
        result = client.create_margin_loan(asset=asset, amount=str(amount))
    except BinanceAPIException as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ 마진 대출 완료")
    print(f"   자산: {asset}")
    print(f"   금액: {format_number(amount)}")
    print(f"   거래 ID: {result.get('tranId')}")


def margin_repay(asset: str, amount: float) -> None:
    """마진 상환"""
    client = get_binance_client()
    asset = asset.upper()

    try:
        result = client.repay_margin_loan(asset=asset, amount=str(amount))
    except BinanceAPIException as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ 마진 상환 완료")
    print(f"   자산: {asset}")
    print(f"   금액: {format_number(amount)}")
    print(f"   거래 ID: {result.get('tranId')}")


def get_max_borrowable(asset: str) -> None:
    """최대 대출 가능 금액 조회"""
    client = get_binance_client()
    asset = asset.upper()

    try:
        result = client.get_max_margin_loan(asset=asset)
    except BinanceAPIException as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)

    amount = float(result.get("amount", 0))
    borrow_limit = float(result.get("borrowLimit", 0))

    print(f"📊 {asset} 마진 대출 정보")
    print(f"   최대 대출 가능: {format_number(amount)}")
    print(f"   대출 한도: {format_number(borrow_limit)}")


def main():
    parser = argparse.ArgumentParser(
        description="바이낸스 마진 대출/상환",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # USDT 100 대출
  %(prog)s borrow USDT 100

  # USDT 100 상환
  %(prog)s repay USDT 100

  # 최대 대출 가능 금액 조회
  %(prog)s info USDT
""",
    )
    parser.add_argument("action", choices=["borrow", "repay", "info"], help="대출/상환/정보")
    parser.add_argument("asset", help="자산 (예: USDT, BTC)")
    parser.add_argument("amount", nargs="?", type=float, help="금액 (info 시 불필요)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.action in ["borrow", "repay"] and not args.amount:
        print(f"Error: {args.action}는 금액이 필요합니다.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        import json

        client = get_binance_client()
        asset = args.asset.upper()
        try:
            if args.action == "borrow":
                result = client.create_margin_loan(asset=asset, amount=str(args.amount))
            elif args.action == "repay":
                result = client.repay_margin_loan(asset=asset, amount=str(args.amount))
            else:  # info
                result = client.get_max_margin_loan(asset=asset)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except BinanceAPIException as e:
            print(json.dumps({"error": e.message, "code": e.code}, indent=2))
            sys.exit(1)
    else:
        if args.action == "borrow":
            margin_borrow(args.asset, args.amount)
        elif args.action == "repay":
            margin_repay(args.asset, args.amount)
        else:
            get_max_borrowable(args.asset)


if __name__ == "__main__":
    main()
