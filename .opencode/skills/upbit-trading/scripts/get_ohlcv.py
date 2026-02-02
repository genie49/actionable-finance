#!/usr/bin/env python3
"""업비트 캔들(OHLCV) 데이터 조회 스크립트"""

import argparse
import sys

import pyupbit


def format_number(num: float) -> str:
    """숫자를 천 단위 구분자로 포맷"""
    if num >= 1:
        return f"{num:,.0f}"
    return f"{num:.8f}".rstrip("0").rstrip(".")


def get_ohlcv(symbol: str, interval: str = "day", count: int = 10) -> None:
    """캔들 데이터 조회"""
    market = f"KRW-{symbol.upper()}" if "-" not in symbol else symbol.upper()

    try:
        df = pyupbit.get_ohlcv(market, interval=interval, count=count)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if df is None or df.empty:
        print(f"Error: {market} 캔들 데이터 조회 실패", file=sys.stderr)
        sys.exit(1)

    print(f"📊 {symbol.upper()} {interval} 캔들 데이터 (최근 {count}개)")
    print("━" * 80)
    print(f"{'일시':^20} {'시가':>12} {'고가':>12} {'저가':>12} {'종가':>12} {'거래량':>10}")
    print("━" * 80)

    for idx, row in df.iterrows():
        date_str = idx.strftime("%Y-%m-%d %H:%M")
        print(
            f"{date_str:^20} "
            f"{format_number(row['open']):>12} "
            f"{format_number(row['high']):>12} "
            f"{format_number(row['low']):>12} "
            f"{format_number(row['close']):>12} "
            f"{row['volume']:>10.2f}"
        )

    print("━" * 80)

    # 간단한 통계
    print(f"\n📈 통계:")
    print(f"   최고가: {format_number(df['high'].max())}원")
    print(f"   최저가: {format_number(df['low'].min())}원")
    print(f"   평균가: {format_number(df['close'].mean())}원")
    print(f"   총 거래량: {format_number(df['volume'].sum())}")


def main():
    parser = argparse.ArgumentParser(description="업비트 캔들(OHLCV) 데이터 조회")
    parser.add_argument("symbol", help="조회할 심볼 (예: BTC)")
    parser.add_argument(
        "--interval",
        "-i",
        default="day",
        choices=["minute1", "minute3", "minute5", "minute10", "minute15", "minute30", "minute60", "minute240", "day", "week", "month"],
        help="캔들 간격 (기본: day)",
    )
    parser.add_argument("--count", "-c", type=int, default=10, help="조회할 캔들 개수 (기본: 10, 최대: 200)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.count > 200:
        args.count = 200
        print("Warning: 최대 200개까지 조회 가능. 200개로 제한됨.", file=sys.stderr)

    if args.json:
        import json

        market = f"KRW-{args.symbol.upper()}" if "-" not in args.symbol else args.symbol.upper()
        df = pyupbit.get_ohlcv(market, interval=args.interval, count=args.count)
        if df is not None:
            df.index = df.index.strftime("%Y-%m-%d %H:%M:%S")
            print(df.to_json(orient="index", indent=2))
    else:
        get_ohlcv(args.symbol, args.interval, args.count)


if __name__ == "__main__":
    main()
