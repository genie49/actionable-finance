#!/usr/bin/env python3
"""한국투자증권 잔고 조회 스크립트"""

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


def get_balance() -> None:
    """잔고 조회"""
    broker = get_kis_broker()

    try:
        resp = broker.fetch_balance()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # rt_cd가 없는 경우도 성공으로 처리 (mojito2 버전에 따라 다름)
    if resp.get("rt_cd") and resp.get("rt_cd") != "0":
        print(f"Error: {resp.get('msg1', '조회 실패')}", file=sys.stderr)
        sys.exit(1)

    output1 = resp.get("output1", [])  # 보유종목
    output2 = resp.get("output2", [{}])[0]  # 계좌 요약

    print("💰 한국투자증권 잔고")
    print("━" * 60)

    # 예수금
    deposit = int(output2.get("dnca_tot_amt", 0))
    print(f"예수금: {format_number(deposit)}원")
    print()

    if not output1:
        print("보유 종목 없음")
    else:
        print("[보유 종목]")
        total_buy = 0
        total_eval = 0
        total_pnl = 0

        for stock in output1:
            code = stock.get("pdno", "")
            name = stock.get("prdt_name", code)
            qty = int(stock.get("hldg_qty", 0))
            avg_price = float(stock.get("pchs_avg_pric", 0))
            current_price = int(stock.get("prpr", 0))
            eval_amt = int(stock.get("evlu_amt", 0))
            pnl_amt = int(stock.get("evlu_pfls_amt", 0))
            pnl_rate = float(stock.get("evlu_pfls_rt", 0))

            buy_amt = avg_price * qty
            total_buy += buy_amt
            total_eval += eval_amt
            total_pnl += pnl_amt

            # 수익률 색상
            if pnl_amt >= 0:
                pnl_str = f"+{format_number(pnl_amt)}원 (+{pnl_rate:.2f}%)"
            else:
                pnl_str = f"{format_number(pnl_amt)}원 ({pnl_rate:.2f}%)"

            print(f"  {name} ({code})")
            print(f"    보유: {qty}주 @ {format_number(avg_price)}원")
            print(f"    현재가: {format_number(current_price)}원")
            print(f"    평가금액: {format_number(eval_amt)}원")
            print(f"    손익: {pnl_str}")
            print()

    print("━" * 60)

    # 총 평가
    total_eval_amt = int(output2.get("tot_evlu_amt", 0))
    total_pnl_amt = int(output2.get("evlu_pfls_smtl_amt", 0))
    total_pnl_rate = float(output2.get("tot_evlu_pfls_rt", 0)) if output2.get("tot_evlu_pfls_rt") else 0

    print(f"💵 총 평가금액: {format_number(total_eval_amt)}원")
    if total_pnl_amt >= 0:
        print(f"📈 총 손익: +{format_number(total_pnl_amt)}원 (+{total_pnl_rate:.2f}%)")
    else:
        print(f"📉 총 손익: {format_number(total_pnl_amt)}원 ({total_pnl_rate:.2f}%)")


def main():
    parser = argparse.ArgumentParser(description="한국투자증권 잔고 조회")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        broker = get_kis_broker()
        try:
            resp = broker.fetch_balance()
            print(json.dumps(resp, indent=2, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2))
            sys.exit(1)
    else:
        get_balance()


if __name__ == "__main__":
    main()
