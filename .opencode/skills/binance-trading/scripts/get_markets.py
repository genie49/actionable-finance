#!/usr/bin/env python3
"""바이낸스 거래 가능 마켓 목록 조회 스크립트"""

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


def get_markets(quote: str | None = None, search: str | None = None) -> None:
    """마켓 목록 조회"""
    load_env()
    client = Client()

    try:
        exchange_info = client.get_exchange_info()
    except BinanceAPIException as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)

    symbols = exchange_info["symbols"]

    # 필터링
    if quote:
        quote = quote.upper()
        symbols = [s for s in symbols if s["quoteAsset"] == quote]

    if search:
        search = search.upper()
        symbols = [s for s in symbols if search in s["symbol"]]

    # 거래 가능한 것만
    symbols = [s for s in symbols if s["status"] == "TRADING"]

    print(f"📊 바이낸스 마켓 목록 ({len(symbols)}개)")
    print("━" * 60)

    # Quote 자산별로 그룹핑
    by_quote: dict[str, list] = {}
    for s in symbols:
        q = s["quoteAsset"]
        if q not in by_quote:
            by_quote[q] = []
        by_quote[q].append(s["baseAsset"])

    for q in sorted(by_quote.keys()):
        bases = sorted(by_quote[q])
        print(f"\n[{q}] ({len(bases)}개)")
        # 한 줄에 10개씩
        for i in range(0, len(bases), 10):
            print("  " + ", ".join(bases[i : i + 10]))

    print("\n" + "━" * 60)
    print(f"총 {len(symbols)}개 마켓")


def main():
    parser = argparse.ArgumentParser(description="바이낸스 마켓 목록 조회")
    parser.add_argument("--quote", "-q", help="기준 통화 필터 (예: USDT, BTC)")
    parser.add_argument("--search", "-s", help="검색어 (예: ETH)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        load_env()
        client = Client()
        try:
            exchange_info = client.get_exchange_info()
            symbols = exchange_info["symbols"]

            if args.quote:
                symbols = [s for s in symbols if s["quoteAsset"] == args.quote.upper()]
            if args.search:
                symbols = [s for s in symbols if args.search.upper() in s["symbol"]]

            symbols = [s for s in symbols if s["status"] == "TRADING"]
            result = [{"symbol": s["symbol"], "base": s["baseAsset"], "quote": s["quoteAsset"]} for s in symbols]
            print(json.dumps(result, indent=2))
        except BinanceAPIException as e:
            print(json.dumps({"error": e.message}, indent=2))
            sys.exit(1)
    else:
        get_markets(args.quote, args.search)


if __name__ == "__main__":
    main()
