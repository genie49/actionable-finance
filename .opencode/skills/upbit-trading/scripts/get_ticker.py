#!/usr/bin/env python3
"""업비트 현재가 조회 스크립트"""

import argparse
import sys

import pyupbit


def format_number(num: float) -> str:
    """숫자를 천 단위 구분자로 포맷"""
    if num >= 1:
        return f"{num:,.0f}"
    return f"{num:.8f}".rstrip("0").rstrip(".")


def get_ticker(symbols: list[str]) -> None:
    """현재가 조회"""
    markets = [f"KRW-{s.upper()}" if "-" not in s else s.upper() for s in symbols]

    try:
        tickers = pyupbit.get_current_price(markets)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if isinstance(tickers, dict):
        for market, price in tickers.items():
            if price is None:
                print(f"  {market}: 조회 실패")
                continue
            symbol = market.split("-")[1]
            print(f"📊 {symbol} 현재가: {format_number(price)}원")
    else:
        symbol = markets[0].split("-")[1]
        print(f"📊 {symbol} 현재가: {format_number(tickers)}원")

    # 상세 정보 조회
    details = pyupbit.get_ohlcv(markets[0], count=1)
    if details is not None and len(details) > 0:
        print()
        for market in markets:
            try:
                ticker_detail = pyupbit.get_current_price(market)
                ohlcv = pyupbit.get_ohlcv(market, count=2)
                if ohlcv is not None and len(ohlcv) >= 2:
                    prev_close = ohlcv.iloc[-2]["close"]
                    curr_price = ticker_detail
                    change = curr_price - prev_close
                    change_pct = (change / prev_close) * 100
                    volume = ohlcv.iloc[-1]["volume"]

                    symbol = market.split("-")[1]
                    sign = "+" if change >= 0 else ""
                    print(f"   {symbol} 전일대비: {sign}{change_pct:.2f}% ({sign}{format_number(change)}원)")
                    print(f"   {symbol} 거래량(24h): {format_number(volume)} {symbol}")
                    print()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="업비트 현재가 조회")
    parser.add_argument("symbols", nargs="+", help="조회할 심볼 (예: BTC ETH XRP)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        markets = [f"KRW-{s.upper()}" if "-" not in s else s.upper() for s in args.symbols]
        tickers = pyupbit.get_current_price(markets)
        print(json.dumps(tickers, indent=2, ensure_ascii=False))
    else:
        get_ticker(args.symbols)


if __name__ == "__main__":
    main()
