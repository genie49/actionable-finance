#!/usr/bin/env python3
"""한국투자증권 주문 내역 조회 스크립트"""

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


def get_orders() -> None:
    """주문 내역 조회"""
    broker = get_kis_broker()

    try:
        resp = broker.fetch_orders()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if resp.get("rt_cd") != "0":
        print(f"Error: {resp.get('msg1', '조회 실패')}", file=sys.stderr)
        sys.exit(1)

    output = resp.get("output", [])

    if not output:
        print("주문 내역 없음")
        return

    print("📋 주문 내역")
    print("━" * 70)

    for order in output:
        order_no = order.get("odno", "")
        code = order.get("pdno", "")
        name = order.get("prdt_name", code)
        side = "매수" if order.get("sll_buy_dvsn_cd") == "02" else "매도"
        order_qty = int(order.get("ord_qty", 0))
        exec_qty = int(order.get("tot_ccld_qty", 0))
        order_price = int(order.get("ord_unpr", 0))
        exec_price = int(order.get("avg_prvs", 0)) if order.get("avg_prvs") else 0
        order_time = order.get("ord_tmd", "")

        # 상태
        if exec_qty == 0:
            status = "🔵 대기"
        elif exec_qty < order_qty:
            status = "🟡 부분체결"
        else:
            status = "🟢 체결완료"

        if order_time:
            order_time = f"{order_time[:2]}:{order_time[2:4]}:{order_time[4:]}"

        print(f"{status} [{name}] {side}")
        print(f"   주문번호: {order_no}")
        print(f"   주문: {order_qty}주 @ {format_number(order_price)}원")
        print(f"   체결: {exec_qty}주", end="")
        if exec_price > 0:
            print(f" @ {format_number(exec_price)}원", end="")
        print()
        print(f"   시간: {order_time}")
        print()

    print(f"━━━ 총 {len(output)}건 ━━━")


def main():
    parser = argparse.ArgumentParser(description="한국투자증권 주문 내역 조회")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        broker = get_kis_broker()
        try:
            resp = broker.fetch_orders()
            print(json.dumps(resp, indent=2, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2))
            sys.exit(1)
    else:
        get_orders()


if __name__ == "__main__":
    main()
