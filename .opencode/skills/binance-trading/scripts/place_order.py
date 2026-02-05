#!/usr/bin/env python3
"""바이낸스 주문 실행 스크립트 (Spot/Margin)

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

from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT
from binance.exceptions import BinanceAPIException


def find_project_root() -> Path:
    """프로젝트 루트 찾기"""
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
    """숫자 포맷"""
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


def to_symbol(ticker: str, quote: str = "USDT") -> str:
    """티커를 바이낸스 심볼로 변환"""
    ticker = ticker.upper()
    if len(ticker) > 5 and (ticker.endswith("USDT") or ticker.endswith("BTC") or ticker.endswith("BUSD")):
        return ticker
    return f"{ticker}{quote}"


def place_order(
    side: str,
    ticker: str,
    quote: str = "USDT",
    price: float | None = None,
    volume: float | None = None,
    quote_amount: float | None = None,
    limit_order: bool = False,
    margin: bool = False,
) -> None:
    """주문 실행"""
    client = get_binance_client()
    symbol = to_symbol(ticker, quote)
    side_enum = SIDE_BUY if side == "buy" else SIDE_SELL

    # 검증
    if side == "buy":
        if limit_order:
            if not price or not volume:
                print("Error: 지정가 매수는 --price와 --volume 모두 필요", file=sys.stderr)
                sys.exit(1)
        else:
            if not quote_amount and not volume:
                print("Error: 시장가 매수는 --quote-amount 또는 --volume 필요", file=sys.stderr)
                sys.exit(1)
    else:  # sell
        if not volume:
            print("Error: 매도는 --volume (수량) 필요", file=sys.stderr)
            sys.exit(1)
        if limit_order and not price:
            print("Error: 지정가 매도는 --price 필요", file=sys.stderr)
            sys.exit(1)

    try:
        # 심볼 정보 조회 (수량 정밀도)
        info = client.get_symbol_info(symbol)
        if not info:
            print(f"Error: {symbol} 심볼 정보를 찾을 수 없습니다.", file=sys.stderr)
            sys.exit(1)

        # LOT_SIZE 필터에서 stepSize 확인
        step_size = None
        min_qty = None
        for f in info["filters"]:
            if f["filterType"] == "LOT_SIZE":
                step_size = float(f["stepSize"])
                min_qty = float(f["minQty"])
                break

        # 시장가 매수 시 quote_amount로 수량 계산
        if side == "buy" and not limit_order and quote_amount:
            current_price = float(client.get_symbol_ticker(symbol=symbol)["price"])
            volume = quote_amount / current_price

        # 수량 정밀도 조정
        if volume and step_size:
            precision = len(str(step_size).rstrip("0").split(".")[-1]) if "." in str(step_size) else 0
            volume = round(volume - (volume % step_size), precision)

        # 최소 수량 체크
        if volume and min_qty and volume < min_qty:
            print(f"Error: 최소 주문 수량은 {min_qty}입니다. (현재: {volume})", file=sys.stderr)
            sys.exit(1)

        # 주문 파라미터
        order_params = {
            "symbol": symbol,
            "side": side_enum,
        }

        if limit_order:
            order_params["type"] = ORDER_TYPE_LIMIT
            order_params["timeInForce"] = "GTC"
            order_params["price"] = str(price)
            order_params["quantity"] = str(volume)
            order_type = "지정가"
        else:
            order_params["type"] = ORDER_TYPE_MARKET
            order_params["quantity"] = str(volume)
            order_type = "시장가"

        # 주문 실행
        if margin:
            result = client.create_margin_order(**order_params)
        else:
            result = client.create_order(**order_params)

    except BinanceAPIException as e:
        print(f"Error: 주문 실패 - {e.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # 성공 출력
    side_kr = "매수" if side == "buy" else "매도"
    account_type = "Margin" if margin else "Spot"

    print(f"✅ {account_type} {side_kr} 주문 완료")
    print(f"   주문번호: {result.get('orderId', 'N/A')}")
    print(f"   심볼: {result.get('symbol', symbol)}")
    print(f"   주문타입: {order_type}")

    if limit_order:
        print(f"   주문가: ${format_number(price)}")
        print(f"   주문량: {format_number(volume)}")
    else:
        print(f"   주문량: {format_number(volume)}")
        # 체결 정보
        if result.get("fills"):
            total_qty = sum(float(f["qty"]) for f in result["fills"])
            total_quote = sum(float(f["qty"]) * float(f["price"]) for f in result["fills"])
            avg_price = total_quote / total_qty if total_qty else 0
            print(f"   체결가(평균): ${format_number(avg_price)}")
            print(f"   체결금액: ${format_number(total_quote)}")

    print(f"   상태: {result.get('status', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(
        description="바이낸스 주문 실행 (주의: 실제 주문이 체결됩니다!)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # Spot 시장가 매수 (100 USDT어치 BTC)
  %(prog)s buy BTC --quote-amount 100

  # Spot 시장가 매도 (0.001 BTC)
  %(prog)s sell BTC --volume 0.001

  # Spot 지정가 매수 (50000 USDT에 0.001 BTC)
  %(prog)s buy BTC --price 50000 --volume 0.001 --limit

  # Margin 시장가 매수
  %(prog)s buy BTC --quote-amount 100 --margin
""",
    )
    parser.add_argument("side", choices=["buy", "sell"], help="매수/매도")
    parser.add_argument("ticker", help="심볼 (예: BTC, ETH)")
    parser.add_argument("--quote", "-q", default="USDT", help="기준 통화 (기본: USDT)")
    parser.add_argument("--price", "-p", type=float, help="지정가 주문 시 가격")
    parser.add_argument("--volume", "-v", type=float, help="주문 수량")
    parser.add_argument("--quote-amount", "-a", type=float, help="매수 금액 (USDT)")
    parser.add_argument("--limit", "-l", action="store_true", help="지정가 주문")
    parser.add_argument("--margin", "-m", action="store_true", help="마진 주문")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    if args.json:
        import json

        # JSON 출력 모드
        client = get_binance_client()
        symbol = to_symbol(args.ticker, args.quote)
        side_enum = SIDE_BUY if args.side == "buy" else SIDE_SELL

        order_params = {
            "symbol": symbol,
            "side": side_enum,
        }

        if args.limit:
            order_params["type"] = ORDER_TYPE_LIMIT
            order_params["timeInForce"] = "GTC"
            order_params["price"] = str(args.price)
            order_params["quantity"] = str(args.volume)
        else:
            order_params["type"] = ORDER_TYPE_MARKET
            if args.volume:
                order_params["quantity"] = str(args.volume)

        try:
            if args.margin:
                result = client.create_margin_order(**order_params)
            else:
                result = client.create_order(**order_params)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except BinanceAPIException as e:
            print(json.dumps({"error": e.message, "code": e.code}, indent=2))
            sys.exit(1)
    else:
        place_order(
            args.side,
            args.ticker,
            args.quote,
            args.price,
            args.volume,
            args.quote_amount,
            args.limit,
            args.margin,
        )


if __name__ == "__main__":
    main()
