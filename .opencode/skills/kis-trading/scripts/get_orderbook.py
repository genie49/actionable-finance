#!/usr/bin/env python3
"""한국투자증권 호가창 조회 스크립트"""

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


def get_orderbook(code: str) -> None:
    """호가창 조회"""
    broker = get_kis_broker()
    code = code.zfill(6)

    try:
        resp = broker.fetch_orderbook(code)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if resp.get("rt_cd") != "0":
        print(f"Error: {resp.get('msg1', '조회 실패')}", file=sys.stderr)
        sys.exit(1)

    output1 = resp.get("output1", {})
    output2 = resp.get("output2", [])

    print(f"📊 [{code}] 호가창")
    print("━" * 50)

    # 매도 호가 (상위 10개, 역순)
    print("  [매도 호가]")
    asks = []
    for i in range(10, 0, -1):
        price = int(output1.get(f"askp{i}", 0))
        qty = int(output1.get(f"askp_rsqn{i}", 0))
        if price > 0:
            asks.append((price, qty))

    for price, qty in asks:
        print(f"    {format_number(price):>12}원  |  {format_number(qty):>10}주")

    print("  " + "─" * 46)

    # 매수 호가 (상위 10개)
    print("  [매수 호가]")
    for i in range(1, 11):
        price = int(output1.get(f"bidp{i}", 0))
        qty = int(output1.get(f"bidp_rsqn{i}", 0))
        if price > 0:
            print(f"    {format_number(price):>12}원  |  {format_number(qty):>10}주")

    print("━" * 50)

    # 총 호가 잔량
    total_ask = int(output1.get("total_askp_rsqn", 0))
    total_bid = int(output1.get("total_bidp_rsqn", 0))
    print(f"매도 총잔량: {format_number(total_ask)}주")
    print(f"매수 총잔량: {format_number(total_bid)}주")


def main():
    parser = argparse.ArgumentParser(description="한국투자증권 호가창 조회")
    parser.add_argument("code", help="종목코드 (예: 005930)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        broker = get_kis_broker()
        code = args.code.zfill(6)
        try:
            resp = broker.fetch_orderbook(code)
            print(json.dumps(resp, indent=2, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2))
            sys.exit(1)
    else:
        get_orderbook(args.code)


if __name__ == "__main__":
    main()
