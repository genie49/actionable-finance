#!/usr/bin/env python3
"""업비트 주문 내역 조회 스크립트"""

import argparse
import os
import sys
from datetime import datetime
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


def get_orders(market: str | None = None, state: str = "wait", limit: int = 10) -> None:
    """주문 내역 조회"""
    upbit = get_upbit_client()

    if market:
        market = f"KRW-{market.upper()}" if "-" not in market else market.upper()

    try:
        # pyupbit의 get_order 메서드 사용
        if state == "wait":
            orders = upbit.get_order(market, state="wait")
        elif state == "done":
            orders = upbit.get_order(market, state="done")
        else:
            orders = upbit.get_order(market)
    except Exception as e:
        print(f"Error: 주문 조회 실패 - {e}", file=sys.stderr)
        sys.exit(1)

    if not orders:
        state_kr = "대기" if state == "wait" else "완료" if state == "done" else "전체"
        print(f"📋 {state_kr} 주문 없음")
        return

    # 리스트가 아니면 리스트로 변환
    if not isinstance(orders, list):
        orders = [orders]

    orders = orders[:limit]

    state_kr = "대기" if state == "wait" else "완료" if state == "done" else "전체"
    print(f"📋 {state_kr} 주문 내역")
    print("━" * 70)

    for order in orders:
        side = "매수" if order.get("side") == "bid" else "매도"
        order_type = "지정가" if order.get("ord_type") == "limit" else "시장가"
        market_name = order.get("market", "N/A")
        symbol = market_name.split("-")[1] if "-" in market_name else market_name

        created_at = order.get("created_at", "")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                created_at = dt.strftime("%m/%d %H:%M")
            except Exception:
                pass

        price = float(order.get("price", 0))
        volume = float(order.get("volume", 0))
        executed_volume = float(order.get("executed_volume", 0))
        remaining = float(order.get("remaining_volume", 0))

        state_text = order.get("state", "")
        state_emoji = {
            "wait": "⏳",
            "done": "✅",
            "cancel": "❌",
        }.get(state_text, "")

        print(f"{state_emoji} [{created_at}] {symbol} {side} ({order_type})")
        print(f"   주문번호: {order.get('uuid', 'N/A')[:8]}...")

        if price > 0:
            print(f"   주문가: {format_number(price)}원")

        print(f"   주문량: {format_number(volume)} / 체결: {format_number(executed_volume)}")

        if remaining > 0:
            print(f"   미체결: {format_number(remaining)}")

        print()

    print("━" * 70)
    print(f"총 {len(orders)}건")


def main():
    parser = argparse.ArgumentParser(description="업비트 주문 내역 조회")
    parser.add_argument("--market", "-m", help="마켓 필터 (예: BTC, ETH)")
    parser.add_argument(
        "--state",
        "-s",
        default="wait",
        choices=["wait", "done", "all"],
        help="주문 상태 (기본: wait)",
    )
    parser.add_argument("--limit", "-l", type=int, default=10, help="조회 개수 (기본: 10)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        upbit = get_upbit_client()
        market = None
        if args.market:
            market = f"KRW-{args.market.upper()}" if "-" not in args.market else args.market.upper()

        if args.state == "all":
            orders = upbit.get_order(market)
        else:
            orders = upbit.get_order(market, state=args.state)

        print(json.dumps(orders, indent=2, ensure_ascii=False))
    else:
        get_orders(args.market, args.state, args.limit)


if __name__ == "__main__":
    main()
