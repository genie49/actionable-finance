#!/usr/bin/env python3
"""한국투자증권 주문 실행 스크립트

주의: 이 스크립트는 실제 주문을 실행합니다!
"""

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
    """한투 브로커 객체 생성"""
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


def place_order(side: str, code: str, qty: int, price: int | None = None) -> None:
    """주문 실행"""
    broker = get_kis_broker()
    code = code.zfill(6)

    try:
        if side == "buy":
            if price:
                # 지정가 매수
                resp = broker.create_limit_buy_order(
                    symbol=code,
                    price=price,
                    quantity=qty,
                )
                order_type = "지정가"
            else:
                # 시장가 매수
                resp = broker.create_market_buy_order(
                    symbol=code,
                    quantity=qty,
                )
                order_type = "시장가"
        else:  # sell
            if price:
                # 지정가 매도
                resp = broker.create_limit_sell_order(
                    symbol=code,
                    price=price,
                    quantity=qty,
                )
                order_type = "지정가"
            else:
                # 시장가 매도
                resp = broker.create_market_sell_order(
                    symbol=code,
                    quantity=qty,
                )
                order_type = "시장가"

    except Exception as e:
        print(f"Error: 주문 실패 - {e}", file=sys.stderr)
        sys.exit(1)

    if resp.get("rt_cd") != "0":
        print(f"Error: {resp.get('msg1', '주문 실패')}", file=sys.stderr)
        sys.exit(1)

    output = resp.get("output", {})
    order_no = output.get("ODNO", "N/A")

    side_kr = "매수" if side == "buy" else "매도"
    print(f"✅ {side_kr} 주문 완료")
    print(f"   종목코드: {code}")
    print(f"   주문번호: {order_no}")
    print(f"   주문타입: {order_type}")
    print(f"   수량: {qty}주")
    if price:
        print(f"   주문가: {format_number(price)}원")


def main():
    parser = argparse.ArgumentParser(
        description="한국투자증권 주문 실행 (주의: 실제 주문이 체결됩니다!)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 시장가 매수 (삼성전자 10주)
  %(prog)s buy 005930 --qty 10

  # 시장가 매도
  %(prog)s sell 005930 --qty 10

  # 지정가 매수 (70,000원에 10주)
  %(prog)s buy 005930 --qty 10 --price 70000

  # 지정가 매도
  %(prog)s sell 005930 --qty 10 --price 75000
""",
    )
    parser.add_argument("side", choices=["buy", "sell"], help="매수/매도")
    parser.add_argument("code", help="종목코드 (예: 005930)")
    parser.add_argument("--qty", "-q", type=int, required=True, help="주문 수량")
    parser.add_argument("--price", "-p", type=int, help="지정가 (미입력시 시장가)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.qty <= 0:
        print("Error: 수량은 1 이상이어야 합니다.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        import json

        broker = get_kis_broker()
        code = args.code.zfill(6)
        try:
            if args.side == "buy":
                if args.price:
                    resp = broker.create_limit_buy_order(code, args.price, args.qty)
                else:
                    resp = broker.create_market_buy_order(code, args.qty)
            else:
                if args.price:
                    resp = broker.create_limit_sell_order(code, args.price, args.qty)
                else:
                    resp = broker.create_market_sell_order(code, args.qty)
            print(json.dumps(resp, indent=2, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2))
            sys.exit(1)
    else:
        place_order(args.side, args.code, args.qty, args.price)


if __name__ == "__main__":
    main()
