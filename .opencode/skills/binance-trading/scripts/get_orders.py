#!/usr/bin/env python3
"""바이낸스 주문 내역 조회 스크립트"""

import argparse
import os
import sys
from datetime import datetime
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


def format_number(num: float, decimals: int = 2) -> str:
    if num >= 1:
        return f"{num:,.{decimals}f}"
    return f"{num:.8f}".rstrip("0").rstrip(".")


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


def get_orders(
    symbol: str | None = None,
    open_only: bool = False,
    margin: bool = False,
    limit: int = 20,
) -> None:
    """주문 내역 조회"""
    client = get_binance_client()

    try:
        if open_only:
            if margin:
                orders = client.get_open_margin_orders(symbol=symbol) if symbol else client.get_open_margin_orders()
            else:
                orders = client.get_open_orders(symbol=symbol) if symbol else client.get_open_orders()
        else:
            if not symbol:
                print("Error: 전체 주문 내역 조회 시 --symbol 필요", file=sys.stderr)
                sys.exit(1)
            if margin:
                orders = client.get_all_margin_orders(symbol=symbol, limit=limit)
            else:
                orders = client.get_all_orders(symbol=symbol, limit=limit)

    except BinanceAPIException as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)

    if not orders:
        print("주문 내역 없음")
        return

    account_type = "Margin" if margin else "Spot"
    order_type = "미체결" if open_only else "전체"

    print(f"📋 {account_type} {order_type} 주문 내역")
    print("━" * 80)

    for order in orders:
        order_id = order["orderId"]
        sym = order["symbol"]
        side = "매수" if order["side"] == "BUY" else "매도"
        order_type_str = order["type"]
        status = order["status"]
        price = float(order["price"]) if float(order["price"]) > 0 else "시장가"
        orig_qty = float(order["origQty"])
        executed_qty = float(order["executedQty"])
        time_str = datetime.fromtimestamp(order["time"] / 1000).strftime("%Y-%m-%d %H:%M:%S")

        status_emoji = {
            "NEW": "🔵",
            "PARTIALLY_FILLED": "🟡",
            "FILLED": "🟢",
            "CANCELED": "⚪",
            "REJECTED": "🔴",
            "EXPIRED": "⚫",
        }.get(status, "⚪")

        print(f"{status_emoji} [{sym}] {side} {order_type_str}")
        print(f"   주문번호: {order_id}")
        print(f"   가격: ${format_number(price) if isinstance(price, float) else price}")
        print(f"   수량: {format_number(orig_qty, 6)} (체결: {format_number(executed_qty, 6)})")
        print(f"   상태: {status}")
        print(f"   시간: {time_str}")
        print()

    print(f"━━━ 총 {len(orders)}건 ━━━")


def main():
    parser = argparse.ArgumentParser(description="바이낸스 주문 내역 조회")
    parser.add_argument("--symbol", "-s", help="심볼 (예: BTCUSDT 또는 BTC)")
    parser.add_argument("--quote", "-q", default="USDT", help="기준 통화 (기본: USDT)")
    parser.add_argument("--open", "-o", action="store_true", help="미체결 주문만")
    parser.add_argument("--margin", "-m", action="store_true", help="마진 주문")
    parser.add_argument("--limit", "-l", type=int, default=20, help="조회 수 (기본: 20)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    symbol = to_symbol(args.symbol, args.quote) if args.symbol else None

    if args.json:
        import json

        client = get_binance_client()
        try:
            if args.open:
                if args.margin:
                    orders = client.get_open_margin_orders(symbol=symbol) if symbol else client.get_open_margin_orders()
                else:
                    orders = client.get_open_orders(symbol=symbol) if symbol else client.get_open_orders()
            else:
                if args.margin:
                    orders = client.get_all_margin_orders(symbol=symbol, limit=args.limit)
                else:
                    orders = client.get_all_orders(symbol=symbol, limit=args.limit)
            print(json.dumps(orders, indent=2, ensure_ascii=False))
        except BinanceAPIException as e:
            print(json.dumps({"error": e.message}, indent=2))
            sys.exit(1)
    else:
        get_orders(symbol, args.open, args.margin, args.limit)


if __name__ == "__main__":
    main()
