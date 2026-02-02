#!/usr/bin/env python3
"""캔들차트 이미지 생성 스크립트"""

import argparse
import sys
import tempfile
from pathlib import Path

try:
    import pandas as pd
    import pyupbit
    import mplfinance as mpf
    import matplotlib.pyplot as plt
except ImportError as e:
    print(f"Error: {e}")
    print("필요한 패키지: pip install mplfinance pandas matplotlib pyupbit")
    sys.exit(1)


# 봉 간격 매핑
INTERVAL_MAP = {
    "1m": "minute1",
    "3m": "minute3",
    "5m": "minute5",
    "10m": "minute10",
    "15m": "minute15",
    "30m": "minute30",
    "1h": "minute60",
    "4h": "minute240",
    "1d": "day",
    "1w": "week",
    "1M": "month",
    # 기존 형식도 지원
    "minute1": "minute1",
    "minute3": "minute3",
    "minute5": "minute5",
    "minute10": "minute10",
    "minute15": "minute15",
    "minute30": "minute30",
    "minute60": "minute60",
    "minute240": "minute240",
    "day": "day",
    "week": "week",
    "month": "month",
}

INTERVAL_DISPLAY = {
    "minute1": "1m",
    "minute3": "3m",
    "minute5": "5m",
    "minute10": "10m",
    "minute15": "15m",
    "minute30": "30m",
    "minute60": "1H",
    "minute240": "4H",
    "day": "1D",
    "week": "1W",
    "month": "1M",
}


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD 계산"""
    exp1 = df["close"].ewm(span=fast, adjust=False).mean()
    exp2 = df["close"].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line

    return pd.DataFrame({
        "MACD": macd,
        "Signal": signal_line,
        "Histogram": histogram,
    }, index=df.index)


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """RSI 계산"""
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def create_chart(
    symbol: str,
    interval: str = "1h",
    count: int = 30,
    ma: list[int] | None = None,
    macd: bool = False,
    rsi: bool = False,
    volume: bool = False,
    output: str | None = None,
) -> str:
    """캔들차트 이미지 생성

    Args:
        symbol: 심볼 (예: BTC)
        interval: 봉 간격 (예: 1h, 1d)
        count: 봉 개수 (기본: 30)
        ma: 이동평균선 기간 리스트 (예: [5, 20, 60])
        macd: MACD 표시 여부
        rsi: RSI 표시 여부
        volume: 거래량 표시 여부
        output: 출력 파일 경로 (없으면 임시 파일)

    Returns:
        생성된 이미지 파일 경로
    """
    # 마켓 코드 변환
    market = f"KRW-{symbol.upper()}" if "-" not in symbol else symbol.upper()

    # 봉 간격 변환
    interval_key = INTERVAL_MAP.get(interval, interval)
    if interval_key not in INTERVAL_MAP.values():
        raise ValueError(f"지원하지 않는 간격: {interval}")

    # 지표 계산을 위해 필요한 추가 데이터 계산
    extra_count = 0
    if ma:
        extra_count = max(extra_count, max(ma))
    if macd:
        extra_count = max(extra_count, 35)  # 26(slow) + 9(signal)
    if rsi:
        extra_count = max(extra_count, 14)

    fetch_count = min(count + extra_count, 200)

    # 캔들 데이터 조회
    df_full = pyupbit.get_ohlcv(market, interval=interval_key, count=fetch_count)
    if df_full is None or df_full.empty:
        raise ValueError(f"{market} 캔들 데이터 조회 실패")

    # mplfinance용 컬럼명 변환
    df_full = df_full.rename(columns={
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    })

    # 추가 플롯 설정 (전체 데이터로 지표 계산 후 트리밍)
    add_plots = []
    panel_ratios = [3, 1] if volume else [3]  # 메인 차트, (거래량)

    # 이동평균선 (전체 데이터로 계산 후 트리밍)
    if ma:
        colors = ["#FFA500", "#00BFFF", "#9370DB", "#32CD32", "#FF69B4"]  # orange, deep sky blue, purple, green, pink
        for i, period in enumerate(ma):
            ma_data = df_full["Close"].rolling(window=period).mean().tail(count)
            add_plots.append(mpf.make_addplot(
                ma_data,
                color=colors[i % len(colors)],
                width=1,
                label=f"MA{period}",
            ))

    # 패널 인덱스 계산 (메인=0, 거래량=1 if volume else 없음)
    next_panel = 2 if volume else 1

    # MACD (전체 데이터로 계산 후 트리밍)
    if macd:
        macd_df = calculate_macd(df_full.rename(columns={"Close": "close"})).tail(count)
        panel_ratios.append(1)
        add_plots.extend([
            mpf.make_addplot(macd_df["MACD"], panel=next_panel, color="#2962FF", width=0.8, ylabel="MACD"),
            mpf.make_addplot(macd_df["Signal"], panel=next_panel, color="#FF6D00", width=0.8),
            mpf.make_addplot(macd_df["Histogram"], panel=next_panel, type="bar", color="#26A69A", alpha=0.5),
        ])
        next_panel += 1

    # RSI (전체 데이터로 계산 후 트리밍)
    if rsi:
        rsi_data = calculate_rsi(df_full.rename(columns={"Close": "close"})).tail(count)
        panel_ratios.append(1)
        add_plots.extend([
            mpf.make_addplot(rsi_data, panel=next_panel, color="#7C4DFF", width=1, ylabel="RSI"),
            mpf.make_addplot([70] * count, panel=next_panel, color="#EF5350", linestyle="--", width=0.5),
            mpf.make_addplot([30] * count, panel=next_panel, color="#26A69A", linestyle="--", width=0.5),
        ])

    # 표시할 데이터만 자르기 (지표 계산 후)
    df = df_full.tail(count)

    # 캔들 색상: 상승=빨강, 하락=파랑 (한국식)
    market_colors = mpf.make_marketcolors(
        up="#EF5350",      # 상승: 빨강
        down="#2962FF",    # 하락: 파랑
        edge="inherit",
        wick="inherit",
        volume={"up": "#EF5350", "down": "#2962FF"},
    )

    # 스타일 설정 (라이트 테마)
    style = mpf.make_mpf_style(
        base_mpf_style="classic",
        marketcolors=market_colors,
        gridstyle="-",
        gridcolor="#E0E0E0",
        facecolor="white",
        edgecolor="black",
        figcolor="white",
        rc={
            "axes.labelsize": 10,
            "axes.titlesize": 12,
            "font.size": 9,
        },
    )

    # 출력 파일 경로
    if output:
        output_path = output
    else:
        tmp_dir = Path(tempfile.gettempdir())
        output_path = str(tmp_dir / f"{symbol.lower()}_{interval_key}_chart.png")

    # 차트 제목
    interval_display = INTERVAL_DISPLAY.get(interval_key, interval_key)
    current_price = df["Close"].iloc[-1]
    price_change = df["Close"].iloc[-1] - df["Close"].iloc[-2]
    price_change_pct = (price_change / df["Close"].iloc[-2]) * 100

    title = f"{symbol.upper()} {interval_display} ({count} candles)"

    # 차트 생성 옵션
    plot_kwargs = {
        "type": "candle",
        "style": style,
        "title": title,
        "ylabel": "Price (KRW)",
        "volume": volume,
        "panel_ratios": panel_ratios,
        "figsize": (12, 8),
        "returnfig": True,
        "tight_layout": True,
    }

    if volume:
        plot_kwargs["ylabel_lower"] = "Volume"

    if add_plots:
        plot_kwargs["addplot"] = add_plots

    fig, axes = mpf.plot(df, **plot_kwargs)

    # 현재가 정보 추가
    price_color = "#EF5350" if price_change >= 0 else "#2962FF"
    price_text = f"Price: {current_price:,.0f} KRW ({price_change_pct:+.2f}%)"
    fig.text(0.99, 0.01, price_text, ha="right", va="bottom", fontsize=10, color=price_color)

    # 지표 범례 추가
    if ma:
        ma_text = "MA: " + ", ".join([f"{p}" for p in ma])
        fig.text(0.01, 0.01, ma_text, ha="left", va="bottom", fontsize=9, color="gray")

    # 저장
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="캔들차트 이미지 생성")
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
        "--output", "-o",
        type=str,
        default=None,
        help="출력 파일 경로 (기본: 임시 파일)",
    )

    args = parser.parse_args()

    # 봉 개수 제한
    if args.count > 200:
        args.count = 200
        print("Warning: 최대 200개까지 조회 가능. 200개로 제한됨.", file=sys.stderr)

    # MA 파싱
    ma_periods = None
    if args.ma:
        try:
            ma_periods = [int(x.strip()) for x in args.ma.split(",")]
        except ValueError:
            print("Error: --ma 옵션은 쉼표로 구분된 숫자여야 합니다 (예: 5,20,60)", file=sys.stderr)
            sys.exit(1)

    try:
        output_path = create_chart(
            symbol=args.symbol,
            interval=args.interval,
            count=args.count,
            ma=ma_periods,
            macd=args.macd,
            rsi=args.rsi,
            volume=args.volume,
            output=args.output,
        )
        print(f"차트 생성 완료: {output_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
