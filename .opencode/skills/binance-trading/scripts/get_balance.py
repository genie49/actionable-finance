#!/usr/bin/env python3
"""바이낸스 잔고 조회 스크립트 (Spot/Margin)"""

import argparse
import os
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


def format_number(num: float, decimals: int = 8) -> str:
    """숫자를 천 단위 구분자로 포맷"""
    if num >= 1:
        return f"{num:,.{min(decimals, 2)}f}"
    return f"{num:.{decimals}f}".rstrip("0").rstrip(".")


def get_binance_client() -> Client:
    """바이낸스 클라이언트 생성"""
    load_env()
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")

    if not api_key or not secret_key:
        print("Error: BINANCE_API_KEY, BINANCE_SECRET_KEY 환경변수를 설정해주세요.", file=sys.stderr)
        sys.exit(1)

    return Client(api_key, secret_key)


def get_spot_balance(client: Client, ticker: str | None = None) -> list[dict]:
    """Spot 잔고 조회"""
    account = client.get_account()
    balances = []

    for balance in account["balances"]:
        free = float(balance["free"])
        locked = float(balance["locked"])
        total = free + locked

        if total > 0:
            if ticker and balance["asset"] != ticker.upper():
                continue
            balances.append({
                "asset": balance["asset"],
                "free": free,
                "locked": locked,
                "total": total,
            })

    return balances


def get_margin_balance(client: Client, ticker: str | None = None) -> list[dict]:
    """Cross Margin 잔고 조회"""
    try:
        account = client.get_margin_account()
    except BinanceAPIException as e:
        if e.code == -3003:  # Margin not enabled
            print("Warning: 마진 계정이 활성화되지 않았습니다.", file=sys.stderr)
            return []
        raise

    balances = []

    for balance in account["userAssets"]:
        free = float(balance["free"])
        locked = float(balance["locked"])
        borrowed = float(balance["borrowed"])
        interest = float(balance["interest"])
        net = float(balance["netAsset"])

        if free > 0 or locked > 0 or borrowed > 0:
            if ticker and balance["asset"] != ticker.upper():
                continue
            balances.append({
                "asset": balance["asset"],
                "free": free,
                "locked": locked,
                "borrowed": borrowed,
                "interest": interest,
                "net": net,
            })

    return balances


def print_spot_balance(balances: list[dict]) -> None:
    """Spot 잔고 출력"""
    print("💰 바이낸스 Spot 잔고")
    print("━" * 50)

    total_usdt = 0
    client = Client()  # 시세 조회용

    for b in balances:
        asset = b["asset"]
        total = b["total"]
        locked = b["locked"]

        # USDT 환산
        if asset == "USDT":
            usdt_value = total
        else:
            try:
                price = client.get_symbol_ticker(symbol=f"{asset}USDT")
                usdt_value = total * float(price["price"])
            except Exception:
                usdt_value = 0

        total_usdt += usdt_value

        print(f"{asset:8}: {format_number(total)}", end="")
        if usdt_value > 0 and asset != "USDT":
            print(f" (${format_number(usdt_value, 2)})", end="")
        if locked > 0:
            print(f" [주문중: {format_number(locked)}]", end="")
        print()

    print("━" * 50)
    print(f"💵 총 평가: ${format_number(total_usdt, 2)}")


def print_margin_balance(balances: list[dict]) -> None:
    """Margin 잔고 출력"""
    print("💳 바이낸스 Cross Margin 잔고")
    print("━" * 50)

    for b in balances:
        asset = b["asset"]
        free = b["free"]
        locked = b["locked"]
        borrowed = b["borrowed"]
        interest = b["interest"]
        net = b["net"]

        print(f"{asset:8}: 가용 {format_number(free)}", end="")
        if locked > 0:
            print(f" / 주문중 {format_number(locked)}", end="")
        if borrowed > 0:
            print(f" / 대출 {format_number(borrowed)}", end="")
            if interest > 0:
                print(f" (이자 {format_number(interest)})", end="")
        print(f" / 순자산 {format_number(net)}")

    print("━" * 50)


def main():
    parser = argparse.ArgumentParser(description="바이낸스 잔고 조회")
    parser.add_argument("--ticker", "-t", help="특정 코인만 조회 (예: BTC)")
    parser.add_argument("--margin", "-m", action="store_true", help="Margin 잔고 조회")
    parser.add_argument("--all", "-a", action="store_true", help="Spot + Margin 모두 조회")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    client = get_binance_client()

    if args.json:
        import json

        result = {}
        if args.margin or args.all:
            result["margin"] = get_margin_balance(client, args.ticker)
        if not args.margin or args.all:
            result["spot"] = get_spot_balance(client, args.ticker)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if not args.margin or args.all:
            spot_balances = get_spot_balance(client, args.ticker)
            if spot_balances:
                print_spot_balance(spot_balances)
            else:
                print("Spot 잔고 없음")
            print()

        if args.margin or args.all:
            margin_balances = get_margin_balance(client, args.ticker)
            if margin_balances:
                print_margin_balance(margin_balances)
            else:
                print("Margin 잔고 없음")


if __name__ == "__main__":
    main()
