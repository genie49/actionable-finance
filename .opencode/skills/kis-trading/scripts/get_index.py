#!/usr/bin/env python3
"""주요 지수 현재가 조회 스크립트"""

import argparse
import json
import sys
from datetime import datetime, timedelta

try:
    import FinanceDataReader as fdr
except ImportError:
    fdr = None

# 주요 지수 정보
INDICES = {
    # 국내
    "kospi": {"symbol": "KS11", "name": "KOSPI", "currency": ""},
    "kosdaq": {"symbol": "KQ11", "name": "KOSDAQ", "currency": ""},
    "kospi200": {"symbol": "KS200", "name": "KOSPI 200", "currency": ""},
    # 미국
    "dow": {"symbol": "DJI", "name": "다우존스", "currency": "$"},
    "nasdaq": {"symbol": "IXIC", "name": "나스닥", "currency": "$"},
    "sp500": {"symbol": "S&P500", "name": "S&P 500", "currency": "$"},
    # 아시아
    "nikkei": {"symbol": "N225", "name": "니케이 225", "currency": "¥"},
    "hsi": {"symbol": "HSI", "name": "항셍", "currency": "HK$"},
    "shanghai": {"symbol": "SSEC", "name": "상해종합", "currency": "¥"},
}

# 별칭
ALIASES = {
    "코스피": "kospi",
    "코스닥": "kosdaq",
    "코스피200": "kospi200",
    "다우": "dow",
    "다우존스": "dow",
    "나스닥": "nasdaq",
    "s&p500": "sp500",
    "s&p": "sp500",
    "니케이": "nikkei",
    "항셍": "hsi",
    "상해": "shanghai",
}


def format_number(num: float, decimals: int = 2) -> str:
    """숫자 포맷"""
    if abs(num) >= 1:
        return f"{num:,.{decimals}f}"
    return f"{num:.{decimals}f}"


def get_index_data(index_key: str) -> dict | None:
    """지수 데이터 조회"""
    if fdr is None:
        print("Error: FinanceDataReader가 설치되어 있지 않습니다.", file=sys.stderr)
        return None

    # 별칭 처리
    key = index_key.lower()
    if key in ALIASES:
        key = ALIASES[key]

    if key not in INDICES:
        print(f"Error: 알 수 없는 지수 '{index_key}'", file=sys.stderr)
        print(f"사용 가능한 지수: {', '.join(INDICES.keys())}", file=sys.stderr)
        return None

    info = INDICES[key]
    symbol = info["symbol"]

    try:
        # 최근 5일 데이터 조회
        end = datetime.now()
        start = end - timedelta(days=10)
        df = fdr.DataReader(symbol, start, end)

        if df.empty:
            print(f"Error: 데이터를 가져올 수 없습니다.", file=sys.stderr)
            return None

        # 최근 데이터
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        close = float(latest["Close"])
        prev_close = float(prev["Close"])
        change = close - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0
        high = float(latest["High"])
        low = float(latest["Low"])
        volume = int(latest["Volume"]) if "Volume" in latest else 0

        return {
            "name": info["name"],
            "symbol": symbol,
            "currency": info["currency"],
            "close": close,
            "change": change,
            "change_pct": change_pct,
            "high": high,
            "low": low,
            "volume": volume,
            "date": str(df.index[-1].date()),
        }
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def display_index(data: dict) -> None:
    """지수 데이터 출력"""
    currency = data["currency"]
    change = data["change"]
    change_pct = data["change_pct"]

    if change >= 0:
        change_str = f"+{format_number(change)}"
        pct_str = f"+{format_number(change_pct)}%"
        emoji = "📈"
    else:
        change_str = f"{format_number(change)}"
        pct_str = f"{format_number(change_pct)}%"
        emoji = "📉"

    print(f"{emoji} [{data['name']}] ({data['symbol']})")
    print(f"   현재: {currency}{format_number(data['close'])}")
    print(f"   전일대비: {change_str} ({pct_str})")
    print(f"   고가: {currency}{format_number(data['high'])} / 저가: {currency}{format_number(data['low'])}")
    if data["volume"]:
        print(f"   거래량: {format_number(data['volume'], 0)}")
    print(f"   기준일: {data['date']}")
    print()


def main():
    parser = argparse.ArgumentParser(description="주요 지수 현재가 조회")
    parser.add_argument("indices", nargs="*", default=["kospi", "kosdaq", "dow", "nasdaq", "sp500"],
                        help="조회할 지수 (기본: 주요 5개)")
    parser.add_argument("--all", "-a", action="store_true", help="모든 지수 조회")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    indices = list(INDICES.keys()) if args.all else args.indices

    results = []
    for idx in indices:
        data = get_index_data(idx)
        if data:
            results.append(data)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("📊 주요 지수 현황")
        print("━" * 50)
        for data in results:
            display_index(data)


if __name__ == "__main__":
    main()
