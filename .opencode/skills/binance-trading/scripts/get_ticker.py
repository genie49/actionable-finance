#!/usr/bin/env python3
"""바이낸스 현재가 조회 스크립트"""

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
    """프로젝트 루트 찾기 (.git 또는 .env 기준)"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_env():
    """프로젝트 루트의 .env 파일 로드"""
    if load_dotenv:
        project_root = find_project_root()
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)


def format_number(num: float, decimals: int = 2) -> str:
    """숫자를 천 단위 구분자로 포맷"""
    if num >= 1:
        return f"{num:,.{decimals}f}"
    return f"{num:.8f}".rstrip("0").rstrip(".")


def to_symbol(ticker: str, quote: str = "USDT") -> str:
    """티커를 바이낸스 심볼로 변환"""
    ticker = ticker.upper()
    # 이미 전체 심볼인 경우 (예: BTCUSDT, ETHBTC)
    if len(ticker) > 5 and (ticker.endswith("USDT") or ticker.endswith("BTC") or ticker.endswith("BUSD")):
        return ticker
    return f"{ticker}{quote}"


def get_ticker(symbols: list[str], quote: str = "USDT") -> None:
    """현재가 조회"""
    load_env()
    client = Client()  # 공개 API는 키 불필요

    for ticker in symbols:
        symbol = to_symbol(ticker, quote)
        try:
            # 24시간 티커 정보
            ticker_24h = client.get_ticker(symbol=symbol)

            current_price = float(ticker_24h["lastPrice"])
            price_change = float(ticker_24h["priceChange"])
            price_change_pct = float(ticker_24h["priceChangePercent"])
            high_24h = float(ticker_24h["highPrice"])
            low_24h = float(ticker_24h["lowPrice"])
            volume_24h = float(ticker_24h["volume"])
            quote_volume = float(ticker_24h["quoteVolume"])

            # 출력
            sign = "+" if price_change >= 0 else ""
            print(f"📊 {symbol} 현재가: ${format_number(current_price)}")
            print(f"   전일대비: {sign}{price_change_pct:.2f}% ({sign}${format_number(price_change)})")
            print(f"   24h 고가: ${format_number(high_24h)}")
            print(f"   24h 저가: ${format_number(low_24h)}")
            print(f"   거래량(24h): {format_number(volume_24h, 4)} {ticker.upper()}")
            print(f"   거래대금(24h): ${format_number(quote_volume)}")
            print()

        except BinanceAPIException as e:
            print(f"Error ({symbol}): {e.message}", file=sys.stderr)
        except Exception as e:
            print(f"Error ({symbol}): {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="바이낸스 현재가 조회")
    parser.add_argument("symbols", nargs="+", help="심볼 (예: BTC ETH)")
    parser.add_argument("--quote", "-q", default="USDT", help="기준 통화 (기본: USDT)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        load_env()
        client = Client()
        results = []
        for ticker in args.symbols:
            symbol = to_symbol(ticker, args.quote)
            try:
                ticker_24h = client.get_ticker(symbol=symbol)
                results.append(ticker_24h)
            except Exception as e:
                results.append({"symbol": symbol, "error": str(e)})
        print(json.dumps(results, indent=2))
    else:
        get_ticker(args.symbols, args.quote)


if __name__ == "__main__":
    main()
