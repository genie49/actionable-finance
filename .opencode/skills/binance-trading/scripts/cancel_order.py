#!/usr/bin/env python3
"""바이낸스 주문 취소 스크립트"""

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


def get_binance_client() -> Client:
    load_env()
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")

    if not api_key or not secret_key:
        print("Error: BINANCE_API_KEY, BINANCE_SECRET_KEY 환경변수를 설정해주세요.", file=sys.stderr)
        sys.exit(1)

    return Client(api_key, secret_key)


def to_symbol(ticker: str, quote: str = "USDT") -> str:
    ticker = ticker.upper()
    if len(ticker) > 5 and (ticker.endswith("USDT") or ticker.endswith("BTC") or ticker.endswith("BUSD")):
        return ticker
    return f"{ticker}{quote}"


def cancel_order(symbol: str, order_id: int, margin: bool = False) -> None:
    """주문 취소"""
    client = get_binance_client()

    try:
        if margin:
            result = client.cancel_margin_order(symbol=symbol, orderId=order_id)
        else:
            result = client.cancel_order(symbol=symbol, orderId=order_id)

    except BinanceAPIException as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)

    account_type = "Margin" if margin else "Spot"
    print(f"✅ {account_type} 주문 취소 완료")
    print(f"   심볼: {result.get('symbol')}")
    print(f"   주문번호: {result.get('orderId')}")
    print(f"   상태: {result.get('status')}")


def main():
    parser = argparse.ArgumentParser(description="바이낸스 주문 취소")
    parser.add_argument("symbol", help="심볼 (예: BTCUSDT 또는 BTC)")
    parser.add_argument("order_id", type=int, help="주문 번호")
    parser.add_argument("--quote", "-q", default="USDT", help="기준 통화 (기본: USDT)")
    parser.add_argument("--margin", "-m", action="store_true", help="마진 주문")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    symbol = to_symbol(args.symbol, args.quote)

    if args.json:
        import json

        client = get_binance_client()
        try:
            if args.margin:
                result = client.cancel_margin_order(symbol=symbol, orderId=args.order_id)
            else:
                result = client.cancel_order(symbol=symbol, orderId=args.order_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except BinanceAPIException as e:
            print(json.dumps({"error": e.message, "code": e.code}, indent=2))
            sys.exit(1)
    else:
        cancel_order(symbol, args.order_id, args.margin)


if __name__ == "__main__":
    main()
