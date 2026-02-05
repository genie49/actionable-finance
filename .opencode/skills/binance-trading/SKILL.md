---
name: binance-trading
description: |
  바이낸스 거래소와 연동하여 암호화폐를 매매하는 스킬.
  python-binance 라이브러리 기반으로 동작하며, Spot/Margin 거래를 지원한다.

  사용 시점:
  - "바이낸스 BTC 현재가 알려줘"
  - "바이낸스 잔고 확인해줘"
  - "바이낸스에서 ETH 0.1개 시장가 매수해줘"
  - "binance buy ETH"
  - "마진으로 BTC 매수해줘"
---

# Binance Trading Skill

바이낸스 거래소 API를 통해 암호화폐 매매 및 시세 조회를 수행한다.
Spot(현물) 및 Margin(마진) 거래를 지원한다.

## 사전 요구사항

1. **python-binance 설치**
   ```bash
   uv add python-binance
   ```

2. **바이낸스 API 키 발급**
   - https://www.binance.com/en/my/settings/api-management 접속
   - API 생성 (Edit Restrictions에서 권한 설정)
   - API Key와 Secret Key 획득
   - 필요한 권한: Enable Reading, Enable Spot & Margin Trading

3. **환경변수 설정** (프로젝트 루트의 `.env` 파일)
   ```bash
   BINANCE_API_KEY=your_api_key
   BINANCE_SECRET_KEY=your_secret_key
   ```

## 스크립트 목록

### 시세 조회

| 스크립트 | 설명 |
|----------|------|
| `get_ticker.py` | 현재가 조회 |
| `get_orderbook.py` | 호가창 조회 |
| `get_ohlcv.py` | 캔들(OHLCV) 데이터 조회 |
| `get_markets.py` | 거래 가능 마켓 목록 |

### 자산 및 주문

| 스크립트 | 설명 |
|----------|------|
| `get_balance.py` | 잔고 조회 (Spot/Margin) |
| `place_order.py` | 주문 실행 (Spot/Margin) |
| `cancel_order.py` | 주문 취소 |
| `get_orders.py` | 주문 내역 조회 |

### 마진 전용

| 스크립트 | 설명 |
|----------|------|
| `margin_loan.py` | 마진 대출/상환 |
| `margin_ltv.py` | LTV 및 청산가 계산 |

## 사용법

### 현재가 조회

```bash
uv run python .opencode/skills/binance-trading/scripts/get_ticker.py BTC
uv run python .opencode/skills/binance-trading/scripts/get_ticker.py ETH XRP SOL
```

### 호가창 조회

```bash
uv run python .opencode/skills/binance-trading/scripts/get_orderbook.py BTC
```

### 캔들 데이터 조회

```bash
# 일봉 200개
uv run python .opencode/skills/binance-trading/scripts/get_ohlcv.py BTC --interval 1d --count 200

# 1시간봉 60개
uv run python .opencode/skills/binance-trading/scripts/get_ohlcv.py ETH --interval 1h --count 60
```

### 잔고 조회

```bash
# Spot 잔고
uv run python .opencode/skills/binance-trading/scripts/get_balance.py

# Margin 잔고
uv run python .opencode/skills/binance-trading/scripts/get_balance.py --margin

# 특정 코인만
uv run python .opencode/skills/binance-trading/scripts/get_balance.py --ticker BTC
```

### 주문 실행

```bash
# Spot 시장가 매수 (100 USDT어치 BTC)
uv run python .opencode/skills/binance-trading/scripts/place_order.py buy BTC --quote-amount 100

# Spot 시장가 매도 (0.001 BTC)
uv run python .opencode/skills/binance-trading/scripts/place_order.py sell BTC --volume 0.001

# Spot 지정가 매수
uv run python .opencode/skills/binance-trading/scripts/place_order.py buy BTC --price 50000 --volume 0.001 --limit

# Margin 시장가 매수
uv run python .opencode/skills/binance-trading/scripts/place_order.py buy BTC --quote-amount 100 --margin
```

### 주문 취소

```bash
uv run python .opencode/skills/binance-trading/scripts/cancel_order.py BTCUSDT <order_id>
```

### 주문 내역 조회

```bash
# 미체결 주문
uv run python .opencode/skills/binance-trading/scripts/get_orders.py --symbol BTCUSDT --open

# 전체 주문 내역
uv run python .opencode/skills/binance-trading/scripts/get_orders.py --symbol BTCUSDT
```

### 마진 대출/상환

```bash
# 대출
uv run python .opencode/skills/binance-trading/scripts/margin_loan.py borrow USDT 100

# 상환
uv run python .opencode/skills/binance-trading/scripts/margin_loan.py repay USDT 100
```

## 마켓 코드 형식

바이낸스 심볼은 `{base}{quote}` 형식:
- `BTCUSDT`: USDT로 비트코인 거래
- `ETHUSDT`: USDT로 이더리움 거래
- `ETHBTC`: BTC로 이더리움 거래

스크립트에서는 편의상 `BTC`, `ETH` 등 심볼만 입력하면 `{심볼}USDT`로 자동 변환됨.

## 캔들 간격 (Interval)

| 값 | 설명 |
|----|------|
| `1m` | 1분 |
| `5m` | 5분 |
| `15m` | 15분 |
| `1h` | 1시간 |
| `4h` | 4시간 |
| `1d` | 1일 |
| `1w` | 1주 |

## 주의사항

1. **API 요청 제한**: 분당 1200 request weight 제한
2. **최소 주문**: 심볼별 최소 주문 금액/수량 존재 (보통 10 USDT 이상)
3. **실제 매매**: `place_order.py`는 실제 주문이 체결됨. 테스트 시 주의
4. **마진 리스크**: 마진 거래는 청산 위험 있음
5. **API Key 보안**: API Key, Secret Key 절대 노출 금지

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| `APIError -2015` | API Key 확인, IP 화이트리스트 확인 |
| `APIError -1013` | 최소 주문 금액/수량 미만 |
| `APIError -2010` | 잔고 부족 |
| `APIError -1121` | 잘못된 심볼 |
