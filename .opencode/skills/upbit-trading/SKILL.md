---
name: upbit-trading
description: |
  업비트 거래소와 연동하여 암호화폐를 매매하는 스킬.
  pyupbit 라이브러리 기반으로 동작하며, 시세 조회, 주문, 잔고 확인 등 전체 기능을 지원한다.

  사용 시점:
  - "비트코인 현재가 알려줘"
  - "내 업비트 잔고 확인해줘"
  - "이더리움 0.1개 시장가 매수해줘"
  - "BTC 호가 보여줘"
  - "upbit buy ETH"
---

# Upbit Trading Skill

업비트 거래소 API를 통해 암호화폐 매매 및 시세 조회를 수행한다.

## 사전 요구사항

1. **pyupbit 설치**
   ```bash
   uv add pyupbit
   ```

2. **업비트 API 키 발급**
   - https://upbit.com/mypage/open_api_management 접속
   - Open API 사용 신청
   - Access Key와 Secret Key 획득
   - 필요한 권한 설정: 자산조회, 주문조회, 주문하기

3. **환경변수 설정** (프로젝트 루트의 `.env` 파일)
   ```bash
   # .env 파일에 추가
   UPBIT_ACCESS_KEY=your_access_key
   UPBIT_SECRET_KEY=your_secret_key
   ```
   
   또는 환경변수로 직접 설정:
   ```bash
   export UPBIT_ACCESS_KEY="your_access_key"
   export UPBIT_SECRET_KEY="your_secret_key"
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
| `get_balance.py` | 잔고 조회 |
| `place_order.py` | 주문 실행 (매수/매도) |
| `cancel_order.py` | 주문 취소 |
| `get_orders.py` | 주문 내역 조회 |

## 사용법

### 현재가 조회

```bash
uv run python .opencode/skills/upbit-trading/scripts/get_ticker.py BTC
uv run python .opencode/skills/upbit-trading/scripts/get_ticker.py ETH XRP SOL
```

### 호가창 조회

```bash
uv run python .opencode/skills/upbit-trading/scripts/get_orderbook.py BTC
```

### 캔들 데이터 조회

```bash
# 일봉 200개
uv run python .opencode/skills/upbit-trading/scripts/get_ohlcv.py BTC --interval day --count 200

# 분봉 60개
uv run python .opencode/skills/upbit-trading/scripts/get_ohlcv.py ETH --interval minute60 --count 60
```

### 잔고 조회

```bash
uv run python .opencode/skills/upbit-trading/scripts/get_balance.py
uv run python .opencode/skills/upbit-trading/scripts/get_balance.py --ticker BTC
```

### 주문 실행

```bash
# 시장가 매수 (10만원어치 비트코인)
uv run python .opencode/skills/upbit-trading/scripts/place_order.py buy BTC --price 100000

# 시장가 매도 (0.001 BTC)
uv run python .opencode/skills/upbit-trading/scripts/place_order.py sell BTC --volume 0.001

# 지정가 매수
uv run python .opencode/skills/upbit-trading/scripts/place_order.py buy BTC --price 50000000 --volume 0.001 --limit

# 지정가 매도
uv run python .opencode/skills/upbit-trading/scripts/place_order.py sell BTC --price 60000000 --volume 0.001 --limit
```

### 주문 취소

```bash
uv run python .opencode/skills/upbit-trading/scripts/cancel_order.py <uuid>
```

### 주문 내역 조회

```bash
# 대기 중인 주문
uv run python .opencode/skills/upbit-trading/scripts/get_orders.py --state wait

# 완료된 주문
uv run python .opencode/skills/upbit-trading/scripts/get_orders.py --state done

# 특정 마켓만
uv run python .opencode/skills/upbit-trading/scripts/get_orders.py --market KRW-BTC
```

## 마켓 코드 형식

업비트 마켓 코드는 `{quote}-{base}` 형식:
- `KRW-BTC`: 원화로 비트코인 거래
- `KRW-ETH`: 원화로 이더리움 거래
- `BTC-ETH`: 비트코인으로 이더리움 거래

스크립트에서는 편의상 `BTC`, `ETH` 등 심볼만 입력하면 `KRW-{심볼}`로 자동 변환됨.

## 출력 형식

### 현재가

```
📊 BTC 현재가: 95,234,000원
   전일대비: +2.34% (+2,178,000원)
   거래량(24h): 1,234.56 BTC
```

### 잔고

```
💰 업비트 잔고
━━━━━━━━━━━━━━━━━━━━
KRW     : 1,234,567원
BTC     : 0.05123456 (4,880,000원)
ETH     : 1.23456789 (4,567,890원)
━━━━━━━━━━━━━━━━━━━━
총 평가: 10,682,457원
```

### 주문 결과

```
✅ 매수 주문 완료
   주문번호: abc123-def456
   마켓: KRW-BTC
   주문가: 시장가
   금액: 100,000원
```

## 주의사항

1. **API 요청 제한**: 초당/분당 요청 수 제한 있음
2. **최소 주문 금액**: KRW 마켓 기준 5,000원 이상
3. **실제 매매**: `place_order.py`는 실제 주문이 체결됨. 테스트 시 주의
4. **API Key 보안**: Access Key, Secret Key 절대 노출 금지

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| `401 Unauthorized` | API Key 확인, 환경변수 설정 확인 |
| `InsufficientFundsAsk` | 잔고 부족 |
| `MinimumOrderError` | 최소 주문 금액(5,000원) 미만 |
| `InvalidMarketError` | 마켓 코드 확인 (KRW-BTC 형식) |
