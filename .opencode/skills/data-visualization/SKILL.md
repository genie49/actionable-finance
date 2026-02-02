---
name: data-visualization
description: |
  금융 데이터 시각화 스킬. 캔들차트, 기술적 지표 등을 이미지로 생성하여 텔레그램으로 전송한다.

  사용 시점:
  - "비트코인 차트 보여줘"
  - "이더리움 1시간봉 차트"
  - "BTC 일봉 차트 MA 포함해서"
  - "ETH 4시간봉 RSI랑 MACD 포함"
---

# Data Visualization Skill

금융 데이터를 캔들차트 이미지로 생성하여 텔레그램으로 전송한다.

## 사전 요구사항

1. **필요 패키지** (pyproject.toml에 포함됨)
   - mplfinance
   - pandas
   - matplotlib
   - pyupbit

2. **환경변수** (텔레그램 전송 시 필요)
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

## 스크립트 목록

| 스크립트 | 설명 |
|----------|------|
| `create_chart.py` | 캔들차트 이미지 생성 |
| `send_chart.py` | 차트 생성 + 텔레그램 전송 |

## 사용법

### 차트 생성 + 텔레그램 전송

```bash
# 기본 (1시간봉, 30개) - 캔들차트만
uv run python .opencode/skills/data-visualization/scripts/send_chart.py BTC

# 일봉 50개
uv run python .opencode/skills/data-visualization/scripts/send_chart.py BTC -i 1d -c 50

# 이동평균선 포함
uv run python .opencode/skills/data-visualization/scripts/send_chart.py BTC --ma 5,20,60

# MACD, RSI 지표 포함
uv run python .opencode/skills/data-visualization/scripts/send_chart.py BTC --macd --rsi

# 모든 옵션
uv run python .opencode/skills/data-visualization/scripts/send_chart.py BTC -i 4h -c 60 --ma 7,25 --macd --rsi
```

### 차트 이미지만 생성 (전송 없이)

```bash
uv run python .opencode/skills/data-visualization/scripts/create_chart.py BTC -i 1h -c 30 -o ./btc_chart.png
```

## 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-i, --interval` | 봉 간격 | 1h |
| `-c, --count` | 봉 개수 (최대 200) | 30 |
| `--ma` | 이동평균선 기간 (쉼표 구분, 예: 5,20,60) | 없음 |
| `-v, --volume` | 거래량 표시 | 없음 |
| `--macd` | MACD 지표 표시 | 없음 |
| `--rsi` | RSI 지표 표시 | 없음 |
| `-l, --line` | 수평선 (가격:색상:라벨) | 없음 |
| `-o, --output` | 출력 파일 경로 | 임시 파일 |

### 봉 간격 옵션

| 값 | 설명 |
|----|------|
| `1m` | 1분봉 |
| `5m` | 5분봉 |
| `15m` | 15분봉 |
| `30m` | 30분봉 |
| `1h` | 1시간봉 |
| `4h` | 4시간봉 |
| `1d` | 일봉 |
| `1w` | 주봉 |
| `1M` | 월봉 |

## 차트 특징

- **캔들 색상**: 상승 빨강, 하락 파랑 (한국식)
- **기본**: 캔들차트만 표시
- **라이트 테마**
- **현재가 및 변동률 표시**

### 옵션 지표

- **Volume (거래량)**: `-v` 또는 `--volume`
- **MA (이동평균선)**: 여러 기간 동시 표시 가능
- **MACD**: MACD 라인, 시그널 라인, 히스토그램
- **RSI**: 과매수(70)/과매도(30) 라인 포함

## 예시

```bash
# "비트코인 1시간봉 차트 보여줘"
uv run python .opencode/skills/data-visualization/scripts/send_chart.py BTC -i 1h

# "이더리움 일봉 차트 MA 5, 20 포함해서"
uv run python .opencode/skills/data-visualization/scripts/send_chart.py ETH -i 1d --ma 5,20

# "XRP 4시간봉 RSI 포함해서 보여줘"
uv run python .opencode/skills/data-visualization/scripts/send_chart.py XRP -i 4h --rsi

# "비트코인 차트에 평단가 140,000,000원 표시해줘"
uv run python .opencode/skills/data-visualization/scripts/send_chart.py BTC -i 1d --line "140000000:red:평단가"

# 여러 수평선 (평단가 + 목표가)
uv run python .opencode/skills/data-visualization/scripts/send_chart.py BTC --line "140000000:red:평단가" --line "150000000:green:목표가"
```
