#!/usr/bin/env python3
"""바이낸스 호가창 조회 스크립트"""

import argparse
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


def format_number(num: float, decimals: int = 2) -> str:
    if num >= 1:
        return f"{num:,.{decimals}f}"
    return f"{num:.8f}".rstrip("0").rstrip(".")


def to_symbol(ticker: str, quote: str = "USDT") -> str:
    ticker = ticker.upper()
    if len(ticker) > 5 and (ticker.endswith("USDT") or ticker.endswith("BTC") or ticker.endswith("BUSD")):
        return ticker
    return f"{ticker}{quote}"


def get_orderbook(ticker: str, quote: str = "USDT", limit: int = 10) -> None:
    """호가창 조회"""
    load_env()
    client = Client()
    symbol = to_symbol(ticker, quote)

    try:
        depth = client.get_order_book(symbol=symbol, limit=limit)
    except BinanceAPIException as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)

    asks = depth["asks"][:limit]  # 매도 호가 (낮은 가격 순)
    bids = depth["bids"][:limit]  # 매수 호가 (높은 가격 순)

    print(f"📊 {symbol} 호가창")
    print("━" * 50)

    # 매도 호가 (역순으로 출력하여 위에서 아래로 가격 하락)
    print("  [매도 호가]")
    for price, qty in reversed(asks):
        price = float(price)
        qty = float(qty)
        total = price * qty
        print(f"    ${format_number(price):>12}  |  {format_number(qty, 6):>12}  (${format_number(total)})")

    print("  " + "─" * 46)

    # 매수 호가
    print("  [매수 호가]")
    for price, qty in bids:
        price = float(price)
        qty = float(qty)
        total = price * qty
        print(f"    ${format_number(price):>12}  |  {format_number(qty, 6):>12}  (${format_number(total)})")

    print("━" * 50)

    # 스프레드 계산
    if asks and bids:
        best_ask = float(asks[0][0])
        best_bid = float(bids[0][0])
        spread = best_ask - best_bid
        spread_pct = (spread / best_bid) * 100
        print(f"스프레드: ${format_number(spread)} ({spread_pct:.4f}%)")


def main():
    parser = argparse.ArgumentParser(description="바이낸스 호가창 조회")
    parser.add_argument("ticker", help="심볼 (예: BTC)")
    parser.add_argument("--quote", "-q", default="USDT", help="기준 통화 (기본: USDT)")
    parser.add_argument("--limit", "-l", type=int, default=10, help="호가 수 (기본: 10)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        load_env()
        client = Client()
        symbol = to_symbol(args.ticker, args.quote)
        try:
            depth = client.get_order_book(symbol=symbol, limit=args.limit)
            print(json.dumps(depth, indent=2))
        except BinanceAPIException as e:
            print(json.dumps({"error": e.message}, indent=2))
            sys.exit(1)
    else:
        get_orderbook(args.ticker, args.quote, args.limit)


if __name__ == "__main__":
    main()
