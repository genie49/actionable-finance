#!/usr/bin/env python3
"""캔들차트 생성 후 텔레그램으로 전송하는 스크립트"""

import argparse
import os
import sys
from pathlib import Path

# 스크립트 디렉토리를 path에 추가
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# 프로젝트 루트 찾기
def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()

PROJECT_ROOT = find_project_root()

try:
    from dotenv import load_dotenv
    import requests
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(1)

# 차트 생성 모듈 임포트
from create_chart import create_chart, INTERVAL_DISPLAY, INTERVAL_MAP


def send_photo(bot_token: str, chat_id: str, photo_path: str, caption: str = None) -> bool:
    """텔레그램 봇으로 이미지 전송"""
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

    photo_file = Path(photo_path)
    if not photo_file.exists():
        print(f"Error: 파일을 찾을 수 없음: {photo_path}")
        return False

    with open(photo_file, "rb") as f:
        files = {"photo": f}
        data = {"chat_id": chat_id}

        if caption:
            if len(caption) > 1024:
                caption = caption[:1021] + "..."
            data["caption"] = caption

        response = requests.post(url, files=files, data=data)
        result = response.json()

        if not result.get("ok"):
            print(f"Error: {result.get('description', 'Unknown error')}")
            return False

    return True


def main():
    parser = argparse.ArgumentParser(description="캔들차트 생성 후 텔레그램 전송")
    parser.add_argument("symbol", help="심볼 (예: BTC)")
    parser.add_argument(
        "--interval", "-i",
        default="1h",
        help="봉 간격 (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M) 기본: 1h",
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=30,
        help="봉 개수 (기본: 30, 최대: 200)",
    )
    parser.add_argument(
        "--ma",
        type=str,
        default=None,
        help="이동평균선 기간 (쉼표 구분, 예: 5,20,60)",
    )
    parser.add_argument(
        "--macd",
        action="store_true",
        help="MACD 표시",
    )
    parser.add_argument(
        "--rsi",
        action="store_true",
        help="RSI 표시",
    )
    parser.add_argument(
        "--volume", "-v",
        action="store_true",
        help="거래량 표시",
    )
    parser.add_argument(
        "--line", "-l",
        type=str,
        action="append",
        help="수평선 (가격:색상:라벨, 예: 50000000:red:평단가)",
    )
    parser.add_argument(
        "--chat-id",
        type=str,
        help="Chat ID (기본: 환경변수)",
    )

    args = parser.parse_args()

    # 환경변수 로드
    load_dotenv(PROJECT_ROOT / ".env")

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = args.chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN이 필요합니다.")
        sys.exit(1)

    if not chat_id:
        print("Error: TELEGRAM_CHAT_ID가 필요합니다.")
        sys.exit(1)

    # 봉 개수 제한
    if args.count > 200:
        args.count = 200

    # MA 파싱
    ma_periods = None
    if args.ma:
        try:
            ma_periods = [int(x.strip()) for x in args.ma.split(",")]
        except ValueError:
            print("Error: --ma 옵션은 쉼표로 구분된 숫자여야 합니다", file=sys.stderr)
            sys.exit(1)

    # 수평선 파싱
    hlines = None
    if args.line:
        hlines = []
        for line_str in args.line:
            parts = line_str.split(":")
            try:
                price = float(parts[0])
                color = parts[1] if len(parts) > 1 else "#FF9800"
                label = parts[2] if len(parts) > 2 else ""
                hlines.append({"price": price, "color": color, "label": label})
            except (ValueError, IndexError):
                print(f"Error: --line 형식 오류: {line_str}", file=sys.stderr)
                sys.exit(1)

    try:
        # 차트 생성
        print(f"차트 생성 중... ({args.symbol} {args.interval})")
        output_path = create_chart(
            symbol=args.symbol,
            interval=args.interval,
            count=args.count,
            ma=ma_periods,
            macd=args.macd,
            rsi=args.rsi,
            volume=args.volume,
            hlines=hlines,
        )
        print(f"차트 생성 완료: {output_path}")

        # 캡션 생성
        interval_key = INTERVAL_MAP.get(args.interval, args.interval)
        interval_display = INTERVAL_DISPLAY.get(interval_key, args.interval)

        caption_parts = [f"{args.symbol.upper()} {interval_display} 차트 ({args.count}개)"]

        if ma_periods:
            caption_parts.append(f"MA: {', '.join(map(str, ma_periods))}")
        if args.volume:
            caption_parts.append("Volume")
        if args.macd:
            caption_parts.append("MACD")
        if args.rsi:
            caption_parts.append("RSI")
        if hlines:
            for line in hlines:
                label = line.get("label", "")
                price = line.get("price", 0)
                if label:
                    caption_parts.append(f"{label}: {price:,.0f}")

        caption = "\n".join(caption_parts)

        # 텔레그램 전송
        print(f"텔레그램 전송 중...")
        if send_photo(bot_token, chat_id, output_path, caption):
            print("전송 완료!")
        else:
            sys.exit(1)

        # 임시 파일 삭제
        Path(output_path).unlink(missing_ok=True)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
