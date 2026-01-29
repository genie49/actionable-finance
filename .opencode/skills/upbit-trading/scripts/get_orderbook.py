#!/usr/bin/env python3
"""업비트 호가창 조회 스크립트"""

import argparse
import sys

import pyupbit


def format_number(num: float) -> str:
    """숫자를 천 단위 구분자로 포맷"""
    if num >= 1:
        return f"{num:,.0f}"
    return f"{num:.8f}".rstrip("0").rstrip(".")


def get_orderbook(symbol: str, depth: int = 5) -> None:
    """호가창 조회"""
    market = f"KRW-{symbol.upper()}" if "-" not in symbol else symbol.upper()

    try:
        orderbook = pyupbit.get_orderbook(market)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not orderbook:
        print(f"Error: {market} 호가 조회 실패", file=sys.stderr)
        sys.exit(1)

    ob = orderbook[0] if isinstance(orderbook, list) else orderbook
    units = ob.get("orderbook_units", [])[:depth]

    print(f"📈 {symbol.upper()} 호가창")
    print("━" * 50)
    print(f"{'매도호가':^15} {'가격':^15} {'매수호가':^15}")
    print("━" * 50)

    # 매도호가 (역순으로 출력)
    for unit in reversed(units):
        ask_price = format_number(unit["ask_price"])
        ask_size = f"{unit['ask_size']:.4f}"
        print(f"{ask_size:>15} {ask_price:^15} {'':15}")

    print("─" * 50)

    # 매수호가
    for unit in units:
        bid_price = format_number(unit["bid_price"])
        bid_size = f"{unit['bid_size']:.4f}"
        print(f"{'':15} {bid_price:^15} {bid_size:<15}")

    print("━" * 50)

    # 총 잔량
    total_ask = sum(u["ask_size"] for u in ob.get("orderbook_units", []))
    total_bid = sum(u["bid_size"] for u in ob.get("orderbook_units", []))
    print(f"총 매도잔량: {total_ask:.4f} | 총 매수잔량: {total_bid:.4f}")


def main():
    parser = argparse.ArgumentParser(description="업비트 호가창 조회")
    parser.add_argument("symbol", help="조회할 심볼 (예: BTC)")
    parser.add_argument("--depth", "-d", type=int, default=5, help="호가 깊이 (기본: 5)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        market = f"KRW-{args.symbol.upper()}" if "-" not in args.symbol else args.symbol.upper()
        orderbook = pyupbit.get_orderbook(market)
        print(json.dumps(orderbook, indent=2, ensure_ascii=False))
    else:
        get_orderbook(args.symbol, args.depth)


if __name__ == "__main__":
    main()
