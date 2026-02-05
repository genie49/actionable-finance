#!/usr/bin/env python3
"""한국투자증권 OHLCV(일봉/분봉) 데이터 조회 스크립트"""

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

import mojito


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


def format_number(num: float) -> str:
    if num >= 1:
        return f"{num:,.0f}"
    return f"{num:.2f}"


def get_kis_broker() -> mojito.KoreaInvestment:
    load_env()

    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    cano = os.getenv("KIS_CANO")
    acnt_prdt_cd = os.getenv("KIS_ACNT_PRDT_CD")

    if not app_key or not app_secret:
        print("Error: KIS_APP_KEY, KIS_APP_SECRET 환경변수를 설정해주세요.", file=sys.stderr)
        sys.exit(1)

    if not cano or not acnt_prdt_cd:
        print("Error: KIS_CANO, KIS_ACNT_PRDT_CD 환경변수를 설정해주세요.", file=sys.stderr)
        sys.exit(1)

    return mojito.KoreaInvestment(
        api_key=app_key,
        api_secret=app_secret,
        acc_no=f"{cano}-{acnt_prdt_cd}",
    )


def get_ohlcv(code: str, period: str = "D", count: int = 30) -> None:
    """OHLCV 데이터 조회"""
    broker = get_kis_broker()
    code = code.zfill(6)

    try:
        if period == "D":
            resp = broker.fetch_ohlcv(
                symbol=code,
                timeframe="D",
                adj_price=True,
            )
        else:
            # 분봉은 별도 API 필요
            print("Error: 분봉은 아직 지원하지 않습니다.", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if resp.get("rt_cd") != "0":
        print(f"Error: {resp.get('msg1', '조회 실패')}", file=sys.stderr)
        sys.exit(1)

    output2 = resp.get("output2", [])

    if not output2:
        print("데이터 없음")
        return

    period_name = "일봉" if period == "D" else "분봉"
    print(f"📊 [{code}] {period_name} (최근 {min(len(output2), count)}개)")
    print("━" * 80)
    print(f"{'날짜':^12} | {'시가':>10} | {'고가':>10} | {'저가':>10} | {'종가':>10} | {'거래량':>12}")
    print("━" * 80)

    for candle in output2[:count]:
        date = candle.get("stck_bsop_date", "")
        if date:
            date = f"{date[:4]}-{date[4:6]}-{date[6:]}"

        open_price = int(candle.get("stck_oprc", 0))
        high = int(candle.get("stck_hgpr", 0))
        low = int(candle.get("stck_lwpr", 0))
        close = int(candle.get("stck_clpr", 0))
        volume = int(candle.get("acml_vol", 0))

        print(
            f"{date:^12} | "
            f"{format_number(open_price):>10} | "
            f"{format_number(high):>10} | "
            f"{format_number(low):>10} | "
            f"{format_number(close):>10} | "
            f"{format_number(volume):>12}"
        )


def main():
    parser = argparse.ArgumentParser(description="한국투자증권 OHLCV 데이터 조회")
    parser.add_argument("code", help="종목코드 (예: 005930)")
    parser.add_argument("--period", "-p", default="D", choices=["D", "W", "M"], help="기간 (D:일봉, W:주봉, M:월봉)")
    parser.add_argument("--count", "-c", type=int, default=30, help="조회 수 (기본: 30)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        broker = get_kis_broker()
        code = args.code.zfill(6)
        try:
            resp = broker.fetch_ohlcv(symbol=code, timeframe=args.period, adj_price=True)
            print(json.dumps(resp, indent=2, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2))
            sys.exit(1)
    else:
        get_ohlcv(args.code, args.period, args.count)


if __name__ == "__main__":
    main()
