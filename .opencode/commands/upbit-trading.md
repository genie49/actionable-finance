---
name: upbit-trading
description: |
  업비트 암호화폐 매매 커맨드.
  /upbit-trading 또는 /trade로 실행.
  
  사용 예시:
  - /trade BTC 현재가
  - /trade 잔고
  - /trade BTC 10만원 매수
---

# Upbit Trading Command

업비트 거래소를 통한 암호화폐 매매 커맨드.

## 사용법

```
/upbit-trading [명령] [인자...]
/trade [명령] [인자...]
```

## 명령어

### 시세 조회

```
/trade BTC               # BTC 현재가
/trade BTC ETH XRP       # 여러 코인 현재가
/trade BTC 호가          # BTC 호가창
/trade BTC 차트          # BTC 일봉 차트 (최근 30일)
/trade 마켓             # 거래 가능 마켓 목록
```

### 잔고 조회

```
/trade 잔고             # 전체 잔고
/trade 잔고 BTC         # BTC 잔고만
```

### 매매 주문

```
# 시장가 매수 (금액 기준)
/trade BTC 10만원 매수
/trade ETH 50000원 매수

# 시장가 매도 (수량 기준)
/trade BTC 0.001 매도
/trade ETH 0.5 매도

# 지정가 매수
/trade BTC 5천만원에 0.001 매수
/trade BTC 50000000 0.001 지정가매수

# 지정가 매도
/trade BTC 6천만원에 0.001 매도
```

### 주문 관리

```
/trade 주문             # 대기 중인 주문
/trade 주문내역         # 완료된 주문
/trade 취소 <uuid>      # 주문 취소
```

## 실행 흐름

1. 커맨드 파싱
2. coin-trading 에이전트 호출
3. 매매의 경우 사용자 확인 요청
4. 결과 출력

## 연동

- **에이전트**: `coin-trading`
- **스킬**: `upbit-trading`

## 주의사항

- 매매 주문은 실제 체결됩니다
- 최소 주문 금액: 5,000원
- API 키 환경변수 필요: `UPBIT_ACCESS_KEY`, `UPBIT_SECRET_KEY`
