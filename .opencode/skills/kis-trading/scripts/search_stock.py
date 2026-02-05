#!/usr/bin/env python3
"""한국투자증권 종목 검색 스크립트 (KRX 전체 종목 지원)"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

try:
    import FinanceDataReader as fdr
except ImportError:
    fdr = None

# 캐시 파일 경로
CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_FILE = CACHE_DIR / "krx_stocks.json"
CACHE_EXPIRY_HOURS = 24


def load_stock_cache() -> dict[str, str] | None:
    """캐시된 종목 데이터 로드"""
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 캐시 만료 체크
        cached_time = datetime.fromisoformat(data.get("timestamp", "2000-01-01"))
        if datetime.now() - cached_time > timedelta(hours=CACHE_EXPIRY_HOURS):
            return None

        return data.get("stocks", {})
    except Exception:
        return None


def save_stock_cache(stocks: dict[str, str]) -> None:
    """종목 데이터 캐시 저장"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "stocks": stocks
        }, f, ensure_ascii=False, indent=2)


def fetch_krx_stocks() -> dict[str, str]:
    """KRX 전체 종목 조회"""
    if fdr is None:
        print("Error: FinanceDataReader가 설치되어 있지 않습니다.", file=sys.stderr)
        print("pip install finance-datareader", file=sys.stderr)
        return {}

    # 캐시 확인
    cached = load_stock_cache()
    if cached:
        return cached

    try:
        df = fdr.StockListing('KRX')
        stocks = {}
        for _, row in df.iterrows():
            code = str(row['Code']).zfill(6)
            name = row['Name']
            stocks[name] = code

        # 캐시 저장
        save_stock_cache(stocks)
        return stocks
    except Exception as e:
        print(f"Error fetching KRX stocks: {e}", file=sys.stderr)
        return {}


def search_stock(query: str, limit: int = 20) -> list[tuple[str, str]]:
    """종목 검색"""
    query = query.strip()
    stocks = fetch_krx_stocks()

    if not stocks:
        print("종목 데이터를 가져올 수 없습니다.", file=sys.stderr)
        return []

    results = []

    # 1. 종목코드로 검색
    if query.isdigit():
        code = query.zfill(6)
        for name, c in stocks.items():
            if c == code:
                results.append((name, code))
                break
        if not results:
            # 코드가 존재하면 알 수 없는 종목으로 표시
            results.append((f"종목코드 {code}", code))

    # 2. 종목명으로 검색
    else:
        query_lower = query.lower()

        # 정확히 일치하는 것 먼저
        for name, code in stocks.items():
            if query_lower == name.lower():
                results.append((name, code))

        # 시작하는 것
        for name, code in stocks.items():
            if name.lower().startswith(query_lower) and (name, code) not in results:
                results.append((name, code))

        # 포함하는 것
        for name, code in stocks.items():
            if query_lower in name.lower() and (name, code) not in results:
                results.append((name, code))

    return results[:limit]


def display_results(query: str, results: list[tuple[str, str]]) -> None:
    """검색 결과 출력"""
    if not results:
        print(f"'{query}' 검색 결과 없음")
        return

    print(f"🔍 '{query}' 검색 결과 ({len(results)}건)")
    print("━" * 40)
    for name, code in results:
        print(f"  {name}: {code}")


def main():
    parser = argparse.ArgumentParser(description="KRX 종목 검색")
    parser.add_argument("query", help="종목명 또는 종목코드")
    parser.add_argument("--limit", "-l", type=int, default=20, help="최대 결과 수 (기본: 20)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    parser.add_argument("--refresh", action="store_true", help="캐시 새로고침")
    args = parser.parse_args()

    # 캐시 새로고침
    if args.refresh and CACHE_FILE.exists():
        CACHE_FILE.unlink()

    results = search_stock(args.query, args.limit)

    if args.json:
        output = [{"name": name, "code": code} for name, code in results]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        display_results(args.query, results)


if __name__ == "__main__":
    main()
