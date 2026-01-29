#!/usr/bin/env python3
"""업비트 주문 실행 스크립트

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


def place_order(
    side: str,
    symbol: str,
    price: float | None = None,
    volume: float | None = None,
    limit_order: bool = False,
) -> None:
    """주문 실행"""
    upbit = get_upbit_client()
    market = f"KRW-{symbol.upper()}" if "-" not in symbol else symbol.upper()

    # 검증
    if side == "buy":
        if limit_order:
            if not price or not volume:
                print("Error: 지정가 매수는 --price와 --volume 모두 필요", file=sys.stderr)
                sys.exit(1)
        else:
            if not price:
                print("Error: 시장가 매수는 --price (금액) 필요", file=sys.stderr)
                sys.exit(1)
    else:  # sell
        if not volume:
            print("Error: 매도는 --volume (수량) 필요", file=sys.stderr)
            sys.exit(1)
        if limit_order and not price:
            print("Error: 지정가 매도는 --price 필요", file=sys.stderr)
            sys.exit(1)

    # 최소 주문 금액 체크
    if side == "buy" and not limit_order and price < 5000:
        print("Error: 최소 주문 금액은 5,000원입니다.", file=sys.stderr)
        sys.exit(1)

    # 주문 실행
    try:
        if side == "buy":
            if limit_order:
                result = upbit.buy_limit_order(market, price, volume)
                order_type = "지정가"
            else:
                result = upbit.buy_market_order(market, price)
                order_type = "시장가"
        else:
            if limit_order:
                result = upbit.sell_limit_order(market, price, volume)
                order_type = "지정가"
            else:
                result = upbit.sell_market_order(market, volume)
                order_type = "시장가"

    except Exception as e:
        print(f"Error: 주문 실패 - {e}", file=sys.stderr)
        sys.exit(1)

    if not result:
        print("Error: 주문 응답 없음", file=sys.stderr)
        sys.exit(1)

    if "error" in result:
        error_msg = result["error"].get("message", "알 수 없는 오류")
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)

    # 성공 출력
    side_kr = "매수" if side == "buy" else "매도"
    print(f"✅ {side_kr} 주문 완료")
    print(f"   주문번호: {result.get('uuid', 'N/A')}")
    print(f"   마켓: {result.get('market', market)}")
    print(f"   주문타입: {order_type}")

    if limit_order:
        print(f"   주문가: {format_number(price)}원")
        print(f"   주문량: {format_number(volume)}")
    elif side == "buy":
        print(f"   주문금액: {format_number(price)}원")
    else:
        print(f"   주문량: {format_number(volume)}")

    print(f"   상태: {result.get('state', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(
        description="업비트 주문 실행 (주의: 실제 주문이 체결됩니다!)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 시장가 매수 (10만원어치 비트코인)
  %(prog)s buy BTC --price 100000

  # 시장가 매도 (0.001 BTC)
  %(prog)s sell BTC --volume 0.001

  # 지정가 매수 (5천만원에 0.001 BTC)
  %(prog)s buy BTC --price 50000000 --volume 0.001 --limit

  # 지정가 매도 (6천만원에 0.001 BTC)
  %(prog)s sell BTC --price 60000000 --volume 0.001 --limit
""",
    )
    parser.add_argument("side", choices=["buy", "sell"], help="매수/매도")
    parser.add_argument("symbol", help="심볼 (예: BTC, ETH)")
    parser.add_argument("--price", "-p", type=float, help="가격 (매수 시 금액, 지정가 시 단가)")
    parser.add_argument("--volume", "-v", type=float, help="수량")
    parser.add_argument("--limit", "-l", action="store_true", help="지정가 주문")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        # JSON 출력 모드에서도 주문 실행
        upbit = get_upbit_client()
        market = f"KRW-{args.symbol.upper()}" if "-" not in args.symbol else args.symbol.upper()

        if args.side == "buy":
            if args.limit:
                result = upbit.buy_limit_order(market, args.price, args.volume)
            else:
                result = upbit.buy_market_order(market, args.price)
        else:
            if args.limit:
                result = upbit.sell_limit_order(market, args.price, args.volume)
            else:
                result = upbit.sell_market_order(market, args.volume)

        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        place_order(args.side, args.symbol, args.price, args.volume, args.limit)


if __name__ == "__main__":
    main()
