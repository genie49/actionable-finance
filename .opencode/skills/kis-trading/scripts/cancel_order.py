#!/usr/bin/env python3
"""한국투자증권 주문 취소 스크립트"""

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


def cancel_order(order_no: str, code: str, qty: int) -> None:
    """주문 취소"""
    broker = get_kis_broker()
    code = code.zfill(6)

    try:
        resp = broker.cancel_order(
            org_no=order_no,
            symbol=code,
            quantity=qty,
            total=True,  # 전량 취소
        )
    except Exception as e:
        print(f"Error: 취소 실패 - {e}", file=sys.stderr)
        sys.exit(1)

    if resp.get("rt_cd") != "0":
        print(f"Error: {resp.get('msg1', '취소 실패')}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ 주문 취소 완료")
    print(f"   원주문번호: {order_no}")
    print(f"   종목코드: {code}")


def main():
    parser = argparse.ArgumentParser(description="한국투자증권 주문 취소")
    parser.add_argument("order_no", help="원주문번호")
    parser.add_argument("--code", "-c", required=True, help="종목코드")
    parser.add_argument("--qty", "-q", type=int, required=True, help="취소 수량")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        broker = get_kis_broker()
        code = args.code.zfill(6)
        try:
            resp = broker.cancel_order(
                org_no=args.order_no,
                symbol=code,
                quantity=args.qty,
                total=True,
            )
            print(json.dumps(resp, indent=2, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2))
            sys.exit(1)
    else:
        cancel_order(args.order_no, args.code, args.qty)


if __name__ == "__main__":
    main()
