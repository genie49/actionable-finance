---
name: kis-trading
description: |
  한국투자증권 API를 통해 국내 주식을 매매하는 스킬.
  mojito2 라이브러리 기반으로 동작하며, 시세 조회, 주문, 잔고 확인을 지원한다.

  사용 시점:
  - "삼성전자 현재가 알려줘"
  - "내 주식 잔고 확인해줘"
  - "삼성전자 10주 시장가 매수해줘"
  - "한투 잔고"
---

# KIS Trading Skill

한국투자증권 API를 통해 국내 주식 매매 및 시세 조회를 수행한다.

## 사전 요구사항

1. **mojito2 설치**
   ```bash
   uv add mojito2
   ```

2. **한국투자증권 API 발급**
   - https://apiportal.koreainvestment.com 접속
   - 회원가입 후 앱 등록
   - APP Key, APP Secret 획득
   - 실전투자/모의투자 선택

3. **환경변수 설정** (프로젝트 루트의 `.env` 파일)
   ```bash
   KIS_APP_KEY=your_app_key
   KIS_APP_SECRET=your_app_secret
   KIS_CANO=12345678          # 계좌번호 앞 8자리
   KIS_ACNT_PRDT_CD=01        # 계좌번호 뒤 2자리
   ```

## 스크립트 목록

### 시세 조회

| 스크립트 | 설명 |
|----------|------|
| `get_price.py` | 현재가 조회 |
| `get_orderbook.py` | 호가창 조회 |
| `get_ohlcv.py` | 일봉/분봉 데이터 조회 |
| `search_stock.py` | 종목 검색 |

### 자산 및 주문

| 스크립트 | 설명 |
|----------|------|
| `get_balance.py` | 잔고/보유종목 조회 |
| `place_order.py` | 주문 실행 (매수/매도) |
| `cancel_order.py` | 주문 취소/정정 |
| `get_orders.py` | 주문 내역 조회 |

## 사용법

### 현재가 조회

```bash
# 종목코드로 조회
uv run python .opencode/skills/kis-trading/scripts/get_price.py 005930

# 여러 종목
uv run python .opencode/skills/kis-trading/scripts/get_price.py 005930 000660 035420
```

### 호가창 조회

```bash
uv run python .opencode/skills/kis-trading/scripts/get_orderbook.py 005930
```

### 일봉/분봉 조회

```bash
# 일봉 100개
uv run python .opencode/skills/kis-trading/scripts/get_ohlcv.py 005930 --period D --count 100

# 분봉 60개
uv run python .opencode/skills/kis-trading/scripts/get_ohlcv.py 005930 --period M --count 60
```

### 종목 검색 (KRX 전체 2,800+ 종목)

```bash
# 종목명 검색
uv run python .opencode/skills/kis-trading/scripts/search_stock.py 삼성전자
uv run python .opencode/skills/kis-trading/scripts/search_stock.py 더본코리아
uv run python .opencode/skills/kis-trading/scripts/search_stock.py 에코프로

# 결과 수 제한
uv run python .opencode/skills/kis-trading/scripts/search_stock.py 한화 --limit 5

# 캐시 새로고침 (24시간 자동 갱신)
uv run python .opencode/skills/kis-trading/scripts/search_stock.py 삼성 --refresh
```

### 잔고 조회

```bash
uv run python .opencode/skills/kis-trading/scripts/get_balance.py
```

### 주문 실행

```bash
# 시장가 매수 (삼성전자 10주)
uv run python .opencode/skills/kis-trading/scripts/place_order.py buy 005930 --qty 10

# 시장가 매도
uv run python .opencode/skills/kis-trading/scripts/place_order.py sell 005930 --qty 10

# 지정가 매수
uv run python .opencode/skills/kis-trading/scripts/place_order.py buy 005930 --qty 10 --price 70000

# 지정가 매도
uv run python .opencode/skills/kis-trading/scripts/place_order.py sell 005930 --qty 10 --price 75000
```

### 주문 취소

```bash
uv run python .opencode/skills/kis-trading/scripts/cancel_order.py <주문번호>
```

### 주문 내역 조회

```bash
uv run python .opencode/skills/kis-trading/scripts/get_orders.py
```

## 주요 종목 코드

| 종목명 | 코드 |
|--------|------|
| 삼성전자 | 005930 |
| SK하이닉스 | 000660 |
| NAVER | 035420 |
| 카카오 | 035720 |
| 삼성SDI | 006400 |
| LG에너지솔루션 | 373220 |
| 현대차 | 005380 |
| 기아 | 000270 |

## 주의사항

1. **장 운영시간**: 09:00 ~ 15:30 (주문 가능)
2. **호가 단위**: 가격대별 호가 단위 상이
3. **최소 주문**: 1주 이상
4. **실전/모의**: 환경변수로 실전/모의투자 구분
5. **API 제한**: 초당 요청 수 제한 있음

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| `접근토큰 발급 실패` | APP Key/Secret 확인 |
| `계좌번호 오류` | CANO, ACNT_PRDT_CD 확인 |
| `주문불가 시간` | 장 운영시간 확인 (09:00~15:30) |
| `호가단위 오류` | 가격대별 호가단위 확인 |
