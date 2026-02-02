---
name: scheduler
description: |
  스케줄러 작업을 관리하는 스킬.

  ⛔ 중요: 아래 규칙을 반드시 따를 것!

  1. "X시에 Y해줘" → 기본값은 일회성! (/jobs/once 사용)
  2. "매일", "평일", "주말" 키워드가 있을 때만 반복 (/jobs 사용)
  3. 오전/오후 모호하면 반드시 물어볼 것!
---

# Scheduler Management Skill

내부 스케줄러 서비스를 관리한다.

---

## 🚨🚨🚨 실행 전 필수 체크리스트 🚨🚨🚨

API 호출 전에 반드시 아래를 확인하세요:

### 체크 1: 일회성인가, 반복인가?

```
사용자 요청에 "매일", "평일", "주말", "매주" 키워드가 있는가?
├─ 없다 → 일회성! → /jobs/once (run_at 사용)
└─ 있다 → 반복! → /jobs (cron 사용)
```

**예시:**
- "4시에 비트코인 알려줘" → 키워드 없음 → **일회성** `/jobs/once`
- "매일 4시에 비트코인 알려줘" → "매일" 있음 → 반복 `/jobs`

### 체크 2: 오전인가, 오후인가?

```
현재 시간이 낮(12시~18시)인가?
├─ 낮이다 + 사용자가 "1~6시" 말함 → 오후로 해석 (13~18시)
└─ 모호하다 → 반드시 물어보기: "오전 4시인가요, 오후 4시(16시)인가요?"
```

---

## API 엔드포인트

모든 요청은 `localhost:8000`으로 전송한다 (내부 전용).

### 작업 목록 조회

```bash
curl -s http://localhost:8000/scheduler/jobs | python -m json.tool
```

### 작업 추가

```bash
curl -s -X POST http://localhost:8000/scheduler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "id": "작업ID",
    "cron": "분 시 일 월 요일",
    "content": "OpenCode에 전달할 프롬프트 내용"
  }' | python -m json.tool
```

**필드 설명:**
- `id`: 작업 고유 ID (영문, 하이픈 사용)
- `cron`: cron 표현식 (분 시 일 월 요일)
- `content`: 스케줄 실행 시 OpenCode에 전달될 프롬프트

**cron 형식 예시:**
- `0 8 * * *` - 매일 08:00
- `0 9 * * 1-5` - 평일 09:00
- `30 14 * * *` - 매일 14:30
- `0 */2 * * *` - 2시간마다

### 일회성 작업 추가

```bash
curl -s -X POST http://localhost:8000/scheduler/jobs/once \
  -H "Content-Type: application/json" \
  -d '{
    "id": "작업ID",
    "run_at": "15:30",
    "content": "OpenCode에 전달할 프롬프트 내용"
  }' | python -m json.tool
```

**run_at 형식:**
- `15:30` - 오늘 15시 30분
- `15:30:00` - 오늘 15시 30분 (초 포함)
- `2024-01-15 15:30` - 특정 날짜/시간

**특징:**
- 지정 시간에 한 번만 실행됨
- 실행 후 자동 삭제

### 단일 작업 조회

```bash
curl -s http://localhost:8000/scheduler/jobs/{작업ID} | python -m json.tool
```

### 작업 삭제

```bash
curl -s -X DELETE http://localhost:8000/scheduler/jobs/{작업ID}
```

### 작업 수동 실행

```bash
curl -s -X POST http://localhost:8000/scheduler/trigger/{작업ID}
```

## 사용 예시

### 예시 1: 현재 스케줄 확인

```bash
curl -s http://localhost:8000/scheduler/jobs | python -m json.tool
```

### 예시 2: 매일 오전 9시에 비트코인 가격 알림 추가

```bash
curl -s -X POST http://localhost:8000/scheduler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "id": "btc-price-alert",
    "cron": "0 9 * * *",
    "content": "비트코인 현재 가격을 조회하고 텔레그램으로 알려줘"
  }' | python -m json.tool
```

### 예시 3: 평일 아침 뉴스 요약 추가

```bash
curl -s -X POST http://localhost:8000/scheduler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "id": "weekday-news",
    "cron": "0 8 * * 1-5",
    "content": "/daily-summary 스킬을 실행해서 오늘의 주요 뉴스를 요약해줘"
  }' | python -m json.tool
```

### 예시 4: 오늘 15시 30분에 비트코인 가격 알림 (일회성)

```bash
curl -s -X POST http://localhost:8000/scheduler/jobs/once \
  -H "Content-Type: application/json" \
  -d '{
    "id": "btc-once",
    "run_at": "15:30",
    "content": "비트코인 현재 가격을 조회하고 텔레그램으로 알려줘"
  }' | python -m json.tool
```

### 예시 5: daily-summary 즉시 실행

```bash
curl -s -X POST http://localhost:8000/scheduler/trigger/daily-summary
```

### 예시 6: 작업 삭제

```bash
curl -s -X DELETE http://localhost:8000/scheduler/jobs/btc-price-alert
```

## 기본 등록 작업

서버 시작 시 자동 등록되는 작업:

| ID | 시간 | Content |
|----|------|---------|
| daily-summary | 매일 08:00 | /daily-summary 스킬을 실행해서 24시간 텔레그램 메시지를 수집하고 요약해줘 |

## 스케줄러 실행 시 동작

스케줄된 시간이 되면:

1. `[스케줄러에 의한 자동 실행]` 프리픽스가 추가됨
2. `content` 내용이 OpenCode에 전달됨
3. OpenCode가 content를 해석하여 작업 수행

**실제 실행되는 프롬프트 예시:**
```
[스케줄러에 의한 자동 실행]

/daily-summary 스킬을 실행해서 24시간 텔레그램 메시지를 수집하고 요약해줘
```

## 주의 사항

- 모든 시간은 `Asia/Seoul` 기준
- 작업 ID는 고유해야 함
- 서버 재시작 시 코드에 정의된 기본 작업만 복원됨
- 동적으로 추가한 작업은 메모리에만 저장 (재시작 시 사라짐)
- content는 명확하고 구체적으로 작성
