#!/usr/bin/env python3
"""바이낸스 마진 LTV 계산 스크립트"""

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
    if abs(num) >= 1:
        return f"{num:,.{decimals}f}"
    return f"{num:.{decimals}f}"


def get_binance_client() -> Client:
    load_env()
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")

    if not api_key or not secret_key:
        print("Error: BINANCE_API_KEY, BINANCE_SECRET_KEY 환경변수를 설정해주세요.", file=sys.stderr)
        sys.exit(1)

    return Client(api_key, secret_key)


def get_asset_price(client: Client, symbol: str) -> float:
    """자산의 USDT 가격 조회"""
    if symbol in ["USDT", "USDC", "DAI", "BUSD", "TUSD", "FDUSD"]:
        return 1.0
    try:
        ticker = client.get_symbol_ticker(symbol=f"{symbol}USDT")
        return float(ticker["price"])
    except Exception:
        return 0.0


def calculate_ltv(json_output: bool = False) -> None:
    """마진 LTV 계산"""
    client = get_binance_client()

    try:
        account = client.get_margin_account()
    except BinanceAPIException as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)

    # 자산별 계산
    assets = []
    total_collateral = 0.0
    total_borrowed = 0.0
    total_interest = 0.0

    for asset in account["userAssets"]:
        free = float(asset["free"])
        locked = float(asset["locked"])
        borrowed = float(asset["borrowed"])
        interest = float(asset["interest"])
        net_asset = float(asset["netAsset"])

        total_amount = free + locked

        if total_amount > 0 or borrowed > 0:
            symbol = asset["asset"]
            price = get_asset_price(client, symbol)

            collateral_value = total_amount * price
            borrowed_value = borrowed * price
            interest_value = interest * price

            total_collateral += collateral_value
            total_borrowed += borrowed_value
            total_interest += interest_value

            assets.append({
                "symbol": symbol,
                "amount": total_amount,
                "price": price,
                "collateral_value": collateral_value,
                "borrowed": borrowed,
                "borrowed_value": borrowed_value,
                "interest": interest,
                "interest_value": interest_value,
                "net_asset": net_asset,
            })

    # LTV 계산
    total_debt = total_borrowed + total_interest
    ltv = (total_debt / total_collateral * 100) if total_collateral > 0 else 0
    collateral_ratio = (total_collateral / total_debt * 100) if total_debt > 0 else float("inf")
    margin_level = float(account.get("marginLevel", 0))

    if json_output:
        import json

        result = {
            "assets": assets,
            "summary": {
                "total_collateral_usd": total_collateral,
                "total_borrowed_usd": total_borrowed,
                "total_interest_usd": total_interest,
                "total_debt_usd": total_debt,
                "ltv_percent": ltv,
                "collateral_ratio_percent": collateral_ratio,
                "margin_level": margin_level,
            },
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # 출력
    print("📊 마진 LTV 계산")
    print("━" * 60)

    # 담보 자산
    print("\n[담보 자산]")
    collateral_assets = [a for a in assets if a["collateral_value"] > 0]
    collateral_assets.sort(key=lambda x: x["collateral_value"], reverse=True)

    for a in collateral_assets:
        print(
            f"  {a['symbol']:8}: {a['amount']:>15,.4f} x ${a['price']:>10,.2f} = ${a['collateral_value']:>12,.2f}"
        )

    print(f"\n  {'담보 총액':12}: ${format_number(total_collateral)}")

    # 대출
    print("\n[대출]")
    borrowed_assets = [a for a in assets if a["borrowed"] > 0]
    for a in borrowed_assets:
        print(f"  {a['symbol']:8}: 원금 ${format_number(a['borrowed_value'])} / 이자 ${format_number(a['interest_value'])}")

    print(f"\n  {'대출 원금':12}: ${format_number(total_borrowed)}")
    print(f"  {'미지급 이자':12}: ${format_number(total_interest)}")
    print(f"  {'대출 총액':12}: ${format_number(total_debt)}")

    # 요약
    print("\n" + "━" * 60)
    print(f"📈 LTV: {ltv:.2f}%")
    print(f"   담보비율 (Collateral Ratio): {collateral_ratio:.2f}%")
    print(f"   바이낸스 Margin Level: {margin_level:.2f}")

    # 청산 경고
    print("\n" + "━" * 60)
    if margin_level < 1.3:
        print("🚨 경고: Margin Level이 1.3 미만입니다! 청산 위험!")
    elif margin_level < 1.5:
        print("⚠️  주의: Margin Level이 1.5 미만입니다.")
    else:
        print("✅ 안전: Margin Level 양호")

    # 청산 시뮬레이션
    if total_borrowed > 0 and collateral_assets:
        # 주요 담보 자산 기준 청산가 계산
        btc_asset = next((a for a in collateral_assets if a["symbol"] == "BTC"), None)
        if btc_asset and btc_asset["amount"] > 0:
            # 청산 margin level = 1.1
            # margin_level = total_collateral / total_debt
            # 1.1 = (btc_value + other_collateral) / total_debt
            # btc_price * btc_amount + other = 1.1 * total_debt
            other_collateral = total_collateral - btc_asset["collateral_value"]
            liquidation_btc_value = 1.1 * total_debt - other_collateral
            if btc_asset["amount"] > 0:
                liquidation_price = liquidation_btc_value / btc_asset["amount"]
                current_price = btc_asset["price"]
                drop_percent = ((current_price - liquidation_price) / current_price) * 100

                print(f"\n[BTC 청산가 시뮬레이션]")
                print(f"  현재 BTC 가격: ${format_number(current_price)}")
                print(f"  청산 예상가: ${format_number(liquidation_price)} ({drop_percent:.1f}% 하락 시)")


def main():
    parser = argparse.ArgumentParser(description="바이낸스 마진 LTV 계산")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    calculate_ltv(args.json)


if __name__ == "__main__":
    main()
