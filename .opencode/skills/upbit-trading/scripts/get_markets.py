#!/usr/bin/env python3
"""업비트 거래 가능 마켓 목록 조회 스크립트"""

import argparse
import sys

import pyupbit


def get_markets(quote: str | None = None, search: str | None = None) -> None:
    """거래 가능 마켓 목록 조회"""
    try:
        tickers = pyupbit.get_tickers()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not tickers:
        print("Error: 마켓 목록 조회 실패", file=sys.stderr)
        sys.exit(1)

    # 필터링
    if quote:
        quote = quote.upper()
        tickers = [t for t in tickers if t.startswith(f"{quote}-")]

    if search:
        search = search.upper()
        tickers = [t for t in tickers if search in t]

    # 그룹화
    krw_markets = sorted([t for t in tickers if t.startswith("KRW-")])
    btc_markets = sorted([t for t in tickers if t.startswith("BTC-")])
    usdt_markets = sorted([t for t in tickers if t.startswith("USDT-")])

    print("📋 업비트 거래 가능 마켓")
    print("━" * 60)

    if krw_markets:
        print(f"\n💰 KRW 마켓 ({len(krw_markets)}개)")
        for i in range(0, len(krw_markets), 5):
            row = krw_markets[i : i + 5]
            print("   " + "  ".join(f"{m.split('-')[1]:>6}" for m in row))

    if btc_markets:
        print(f"\n🪙 BTC 마켓 ({len(btc_markets)}개)")
        for i in range(0, len(btc_markets), 5):
            row = btc_markets[i : i + 5]
            print("   " + "  ".join(f"{m.split('-')[1]:>6}" for m in row))

    if usdt_markets:
        print(f"\n💵 USDT 마켓 ({len(usdt_markets)}개)")
        for i in range(0, len(usdt_markets), 5):
            row = usdt_markets[i : i + 5]
            print("   " + "  ".join(f"{m.split('-')[1]:>6}" for m in row))

    print("\n" + "━" * 60)
    print(f"총 {len(tickers)}개 마켓")


def main():
    parser = argparse.ArgumentParser(description="업비트 거래 가능 마켓 목록 조회")
    parser.add_argument("--quote", "-q", help="기준 통화 필터 (KRW, BTC, USDT)")
    parser.add_argument("--search", "-s", help="심볼 검색")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        tickers = pyupbit.get_tickers()
        if args.quote:
            tickers = [t for t in tickers if t.startswith(f"{args.quote.upper()}-")]
        if args.search:
            tickers = [t for t in tickers if args.search.upper() in t]
        print(json.dumps(tickers, indent=2))
    else:
        get_markets(args.quote, args.search)


if __name__ == "__main__":
    main()
