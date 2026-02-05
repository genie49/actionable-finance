#!/usr/bin/env python3
"""바이낸스 OHLCV(캔들) 데이터 조회 스크립트"""

import argparse
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


def to_symbol(ticker: str, quote: str = "USDT") -> str:
    ticker = ticker.upper()
    if len(ticker) > 5 and (ticker.endswith("USDT") or ticker.endswith("BTC") or ticker.endswith("BUSD")):
        return ticker
    return f"{ticker}{quote}"


# 바이낸스 캔들 간격 매핑
INTERVAL_MAP = {
    "1m": Client.KLINE_INTERVAL_1MINUTE,
    "3m": Client.KLINE_INTERVAL_3MINUTE,
    "5m": Client.KLINE_INTERVAL_5MINUTE,
    "15m": Client.KLINE_INTERVAL_15MINUTE,
    "30m": Client.KLINE_INTERVAL_30MINUTE,
    "1h": Client.KLINE_INTERVAL_1HOUR,
    "2h": Client.KLINE_INTERVAL_2HOUR,
    "4h": Client.KLINE_INTERVAL_4HOUR,
    "6h": Client.KLINE_INTERVAL_6HOUR,
    "8h": Client.KLINE_INTERVAL_8HOUR,
    "12h": Client.KLINE_INTERVAL_12HOUR,
    "1d": Client.KLINE_INTERVAL_1DAY,
    "3d": Client.KLINE_INTERVAL_3DAY,
    "1w": Client.KLINE_INTERVAL_1WEEK,
    "1M": Client.KLINE_INTERVAL_1MONTH,
}


def get_ohlcv(ticker: str, quote: str = "USDT", interval: str = "1d", count: int = 100) -> None:
    """OHLCV 데이터 조회"""
    load_env()
    client = Client()
    symbol = to_symbol(ticker, quote)

    if interval not in INTERVAL_MAP:
        print(f"Error: 지원하지 않는 간격: {interval}", file=sys.stderr)
        print(f"지원 간격: {', '.join(INTERVAL_MAP.keys())}", file=sys.stderr)
        sys.exit(1)

    try:
        klines = client.get_klines(
            symbol=symbol,
            interval=INTERVAL_MAP[interval],
            limit=count,
        )
    except BinanceAPIException as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)

    print(f"📊 {symbol} {interval} 캔들 (최근 {len(klines)}개)")
    print("━" * 80)
    print(f"{'시간':^20} | {'시가':>12} | {'고가':>12} | {'저가':>12} | {'종가':>12} | {'거래량':>12}")
    print("━" * 80)

    for kline in klines[-20:]:  # 최근 20개만 출력
        open_time = datetime.fromtimestamp(kline[0] / 1000).strftime("%Y-%m-%d %H:%M")
        open_price = float(kline[1])
        high = float(kline[2])
        low = float(kline[3])
        close = float(kline[4])
        volume = float(kline[5])

        print(
            f"{open_time:^20} | "
            f"${format_number(open_price):>11} | "
            f"${format_number(high):>11} | "
            f"${format_number(low):>11} | "
            f"${format_number(close):>11} | "
            f"{format_number(volume, 4):>12}"
        )

    if len(klines) > 20:
        print(f"... (총 {len(klines)}개 중 최근 20개만 표시)")


def main():
    parser = argparse.ArgumentParser(description="바이낸스 OHLCV(캔들) 데이터 조회")
    parser.add_argument("ticker", help="심볼 (예: BTC)")
    parser.add_argument("--quote", "-q", default="USDT", help="기준 통화 (기본: USDT)")
    parser.add_argument(
        "--interval",
        "-i",
        default="1d",
        choices=list(INTERVAL_MAP.keys()),
        help="캔들 간격 (기본: 1d)",
    )
    parser.add_argument("--count", "-c", type=int, default=100, help="캔들 수 (기본: 100, 최대: 1000)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        load_env()
        client = Client()
        symbol = to_symbol(args.ticker, args.quote)
        try:
            klines = client.get_klines(
                symbol=symbol,
                interval=INTERVAL_MAP[args.interval],
                limit=args.count,
            )
            # OHLCV 포맷으로 변환
            result = []
            for k in klines:
                result.append({
                    "timestamp": k[0],
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                    "close_time": k[6],
                    "quote_volume": float(k[7]),
                    "trades": k[8],
                })
            print(json.dumps(result, indent=2))
        except BinanceAPIException as e:
            print(json.dumps({"error": e.message}, indent=2))
            sys.exit(1)
    else:
        get_ohlcv(args.ticker, args.quote, args.interval, args.count)


if __name__ == "__main__":
    main()
