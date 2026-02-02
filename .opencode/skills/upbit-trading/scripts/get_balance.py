#!/usr/bin/env python3
"""업비트 잔고 조회 스크립트"""

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

import pyupbit


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


def format_number(num: float) -> str:
    """숫자를 천 단위 구분자로 포맷"""
    if num >= 1:
        return f"{num:,.0f}"
    return f"{num:.8f}".rstrip("0").rstrip(".")


def get_upbit_client():
    """업비트 클라이언트 생성"""
    load_env()
    access_key = os.getenv("UPBIT_ACCESS_KEY")
    secret_key = os.getenv("UPBIT_SECRET_KEY")

    if not access_key or not secret_key:
        print("Error: UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY 환경변수를 설정해주세요.", file=sys.stderr)
        sys.exit(1)

    return pyupbit.Upbit(access_key, secret_key)


def get_balance(ticker: str | None = None) -> None:
    """잔고 조회"""
    upbit = get_upbit_client()

    try:
        balances = upbit.get_balances()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not balances:
        print("Error: 잔고 조회 실패", file=sys.stderr)
        sys.exit(1)

    # 특정 코인만 필터
    if ticker:
        ticker = ticker.upper()
        balances = [b for b in balances if b["currency"] == ticker]
        if not balances:
            print(f"Error: {ticker} 잔고 없음", file=sys.stderr)
            sys.exit(1)

    print("💰 업비트 잔고")
    print("━" * 50)

    total_krw_value = 0

    for balance in balances:
        currency = balance["currency"]
        balance_amount = float(balance["balance"])
        locked = float(balance["locked"])
        total = balance_amount + locked

        if total == 0:
            continue

        if currency == "KRW":
            krw_value = total
            total_krw_value += krw_value
            print(f"KRW     : {format_number(total)}원", end="")
            if locked > 0:
                print(f" (주문중: {format_number(locked)}원)", end="")
            print()
        else:
            # 현재가 조회
            try:
                current_price = pyupbit.get_current_price(f"KRW-{currency}")
                if current_price:
                    krw_value = total * current_price
                    total_krw_value += krw_value
                    print(f"{currency:8}: {format_number(total)} ({format_number(krw_value)}원)", end="")
                else:
                    print(f"{currency:8}: {format_number(total)}", end="")
            except Exception:
                print(f"{currency:8}: {format_number(total)}", end="")

            if locked > 0:
                print(f" (주문중: {format_number(locked)})", end="")
            print()

            # 평균 매수가 정보
            avg_buy_price = float(balance.get("avg_buy_price", 0))
            if avg_buy_price > 0 and current_price:
                profit_rate = ((current_price - avg_buy_price) / avg_buy_price) * 100
                sign = "+" if profit_rate >= 0 else ""
                print(f"          평단가: {format_number(avg_buy_price)}원 ({sign}{profit_rate:.2f}%)")

    print("━" * 50)
    print(f"💵 총 평가: {format_number(total_krw_value)}원")


def main():
    parser = argparse.ArgumentParser(description="업비트 잔고 조회")
    parser.add_argument("--ticker", "-t", help="특정 코인만 조회 (예: BTC)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        upbit = get_upbit_client()
        balances = upbit.get_balances()
        if args.ticker:
            balances = [b for b in balances if b["currency"] == args.ticker.upper()]
        print(json.dumps(balances, indent=2, ensure_ascii=False))
    else:
        get_balance(args.ticker)


if __name__ == "__main__":
    main()
