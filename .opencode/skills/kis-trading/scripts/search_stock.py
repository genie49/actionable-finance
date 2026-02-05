#!/usr/bin/env python3
"""한국투자증권 종목 검색 스크립트 (KRX 주식 + ETF + 지수 지원)"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

try:
    import FinanceDataReader as fdr
except ImportError:
    fdr = None

# 캐시 파일 경로
CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_FILE = CACHE_DIR / "krx_all.json"
CACHE_EXPIRY_HOURS = 24

# 주요 지수 정보
INDICES = {
    "코스피": {"symbol": "KS11", "name": "KOSPI 종합"},
    "kospi": {"symbol": "KS11", "name": "KOSPI 종합"},
    "코스닥": {"symbol": "KQ11", "name": "KOSDAQ 종합"},
    "kosdaq": {"symbol": "KQ11", "name": "KOSDAQ 종합"},
    "코스피200": {"symbol": "KS200", "name": "KOSPI 200"},
    "kospi200": {"symbol": "KS200", "name": "KOSPI 200"},
    "다우": {"symbol": "DJI", "name": "다우존스 산업평균"},
    "다우존스": {"symbol": "DJI", "name": "다우존스 산업평균"},
    "나스닥": {"symbol": "IXIC", "name": "나스닥 종합"},
    "nasdaq": {"symbol": "IXIC", "name": "나스닥 종합"},
    "s&p500": {"symbol": "S&P500", "name": "S&P 500"},
    "s&p": {"symbol": "S&P500", "name": "S&P 500"},
    "니케이": {"symbol": "N225", "name": "니케이 225"},
    "항셍": {"symbol": "HSI", "name": "항셍 지수"},
    "상해": {"symbol": "SSEC", "name": "상해 종합"},
}


def load_cache() -> dict | None:
    """캐시된 데이터 로드"""
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        cached_time = datetime.fromisoformat(data.get("timestamp", "2000-01-01"))
        if datetime.now() - cached_time > timedelta(hours=CACHE_EXPIRY_HOURS):
            return None

        return data
    except Exception:
        return None


def save_cache(data: dict) -> None:
    """데이터 캐시 저장"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["timestamp"] = datetime.now().isoformat()
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_all_listings() -> dict:
    """KRX 주식 + ETF 전체 조회"""
    if fdr is None:
        print("Error: FinanceDataReader가 설치되어 있지 않습니다.", file=sys.stderr)
        return {"stocks": {}, "etfs": {}}

    cached = load_cache()
    if cached and "stocks" in cached and "etfs" in cached:
        return {"stocks": cached["stocks"], "etfs": cached["etfs"]}

    result = {"stocks": {}, "etfs": {}}

    try:
        # 주식
        df_stocks = fdr.StockListing('KRX')
        for _, row in df_stocks.iterrows():
            code = str(row['Code']).zfill(6)
            name = row['Name']
            result["stocks"][name] = code

        # ETF
        df_etf = fdr.StockListing('ETF/KR')
        for _, row in df_etf.iterrows():
            code = str(row['Symbol']).zfill(6)
            name = row['Name']
            result["etfs"][name] = code

        save_cache(result)
        return result
    except Exception as e:
        print(f"Error fetching listings: {e}", file=sys.stderr)
        return result


def search_index(query: str) -> list[tuple[str, str, str]]:
    """지수 검색"""
    query_lower = query.lower()
    results = []

    # 직접 매칭
    if query_lower in INDICES:
        info = INDICES[query_lower]
        results.append((info["name"], info["symbol"], "지수"))
        return results

    # 부분 매칭
    for key, info in INDICES.items():
        if query_lower in key or query_lower in info["name"].lower():
            if (info["name"], info["symbol"], "지수") not in results:
                results.append((info["name"], info["symbol"], "지수"))

    return results


def search_all(query: str, limit: int = 20, search_type: str = "all") -> list[tuple[str, str, str]]:
    """통합 검색 (주식 + ETF + 지수)"""
    query = query.strip()
    results = []

    # 지수 검색
    if search_type in ["all", "index"]:
        index_results = search_index(query)
        results.extend(index_results)

    # 주식/ETF 검색
    if search_type in ["all", "stock", "etf"]:
        data = fetch_all_listings()
        stocks = data.get("stocks", {}) if search_type in ["all", "stock"] else {}
        etfs = data.get("etfs", {}) if search_type in ["all", "etf"] else {}

        # 종목코드로 검색
        if query.isdigit():
            code = query.zfill(6)
            for name, c in stocks.items():
                if c == code:
                    results.append((name, code, "주식"))
                    break
            for name, c in etfs.items():
                if c == code:
                    results.append((name, code, "ETF"))
                    break

        # 종목명으로 검색
        else:
            query_lower = query.lower()

            # 정확히 일치
            for name, code in stocks.items():
                if query_lower == name.lower():
                    results.append((name, code, "주식"))
            for name, code in etfs.items():
                if query_lower == name.lower():
                    results.append((name, code, "ETF"))

            # 시작하는 것
            for name, code in stocks.items():
                if name.lower().startswith(query_lower) and (name, code, "주식") not in results:
                    results.append((name, code, "주식"))
            for name, code in etfs.items():
                if name.lower().startswith(query_lower) and (name, code, "ETF") not in results:
                    results.append((name, code, "ETF"))

            # 포함하는 것
            for name, code in stocks.items():
                if query_lower in name.lower() and (name, code, "주식") not in results:
                    results.append((name, code, "주식"))
            for name, code in etfs.items():
                if query_lower in name.lower() and (name, code, "ETF") not in results:
                    results.append((name, code, "ETF"))

    return results[:limit]


def display_results(query: str, results: list[tuple[str, str, str]]) -> None:
    """검색 결과 출력"""
    if not results:
        print(f"'{query}' 검색 결과 없음")
        return

    print(f"🔍 '{query}' 검색 결과 ({len(results)}건)")
    print("━" * 50)
    for name, code, type_ in results:
        type_emoji = {"주식": "📈", "ETF": "📊", "지수": "📉"}.get(type_, "")
        print(f"  {type_emoji} [{type_}] {name}: {code}")


def main():
    parser = argparse.ArgumentParser(description="KRX 종목/ETF/지수 검색")
    parser.add_argument("query", help="종목명, 종목코드, 또는 지수명")
    parser.add_argument("--type", "-t", choices=["all", "stock", "etf", "index"], default="all",
                        help="검색 유형 (all: 전체, stock: 주식, etf: ETF, index: 지수)")
    parser.add_argument("--limit", "-l", type=int, default=20, help="최대 결과 수 (기본: 20)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    parser.add_argument("--refresh", action="store_true", help="캐시 새로고침")
    args = parser.parse_args()

    # 캐시 새로고침
    if args.refresh and CACHE_FILE.exists():
        CACHE_FILE.unlink()

    results = search_all(args.query, args.limit, args.type)

    if args.json:
        output = [{"name": name, "code": code, "type": type_} for name, code, type_ in results]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        display_results(args.query, results)


if __name__ == "__main__":
    main()
