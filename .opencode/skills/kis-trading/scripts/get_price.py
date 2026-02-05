#!/usr/bin/env python3
"""한국투자증권 현재가 조회 스크립트"""

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
    """숫자를 천 단위 구분자로 포맷"""
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


def get_price(codes: list[str]) -> None:
    """현재가 조회"""
    broker = get_kis_broker()

    for code in codes:
        code = code.zfill(6)  # 6자리로 패딩

        try:
            resp = broker.fetch_price(code)

            if resp.get("rt_cd") != "0":
                print(f"Error ({code}): {resp.get('msg1', '조회 실패')}", file=sys.stderr)
                continue

            output = resp.get("output", {})

            name = output.get("stck_shrn_iscd", code)  # 종목명이 없으면 코드
            current = int(output.get("stck_prpr", 0))
            change = int(output.get("prdy_vrss", 0))
            change_pct = float(output.get("prdy_ctrt", 0))
            high = int(output.get("stck_hgpr", 0))
            low = int(output.get("stck_lwpr", 0))
            volume = int(output.get("acml_vol", 0))
            trade_amount = int(output.get("acml_tr_pbmn", 0))

            # 등락 기호
            sign = output.get("prdy_vrss_sign", "3")
            if sign in ["1", "2"]:
                change_str = f"+{change:,}"
                pct_str = f"+{change_pct:.2f}%"
            elif sign in ["4", "5"]:
                change_str = f"-{abs(change):,}"
                pct_str = f"-{abs(change_pct):.2f}%"
            else:
                change_str = "0"
                pct_str = "0.00%"

            print(f"📊 [{code}] 현재가: {format_number(current)}원")
            print(f"   전일대비: {change_str}원 ({pct_str})")
            print(f"   고가: {format_number(high)}원 / 저가: {format_number(low)}원")
            print(f"   거래량: {format_number(volume)}주")
            print(f"   거래대금: {format_number(trade_amount / 1_000_000)}백만원")
            print()

        except Exception as e:
            print(f"Error ({code}): {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="한국투자증권 현재가 조회")
    parser.add_argument("codes", nargs="+", help="종목코드 (예: 005930)")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        broker = get_kis_broker()
        results = []
        for code in args.codes:
            code = code.zfill(6)
            try:
                resp = broker.fetch_price(code)
                results.append({"code": code, "data": resp})
            except Exception as e:
                results.append({"code": code, "error": str(e)})
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        get_price(args.codes)


if __name__ == "__main__":
    main()
