---
name: scheduler
description: |
  스케줄러 작업을 관리하는 스킬.
  작업 조회, 추가, 삭제, 수동 실행이 가능하다.

  사용 시점:
  - "스케줄 목록 보여줘"
  - "매일 9시에 XX 실행하도록 추가해줘"
  - "스케줄 삭제해줘"
  - "지금 당장 daily-summary 실행해줘"
---

# Scheduler Management Skill

내부 스케줄러 서비스를 관리한다. FastAPI 서버의 `/scheduler/*` 엔드포인트를 통해 작업을 제어한다.

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
    "command": "/스킬명"
  }' | python -m json.tool
```

**cron 형식 예시:**
- `0 8 * * *` - 매일 08:00
- `0 9 * * 1-5` - 평일 09:00
- `30 14 * * *` - 매일 14:30
- `0 */2 * * *` - 2시간마다

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

### 예시 2: 매일 오전 9시에 업비트 리포트 추가

```bash
curl -s -X POST http://localhost:8000/scheduler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "id": "upbit-report",
    "cron": "0 9 * * *",
    "command": "/upbit-trading"
  }' | python -m json.tool
```

### 예시 3: daily-summary 즉시 실행

```bash
curl -s -X POST http://localhost:8000/scheduler/trigger/daily-summary
```

### 예시 4: 작업 삭제

```bash
curl -s -X DELETE http://localhost:8000/scheduler/jobs/upbit-report
```

## 기본 등록 작업

서버 시작 시 자동 등록되는 작업:

| ID | 시간 | 명령 |
|----|------|------|
| daily-summary | 매일 08:00 | /daily-summary |

## 주의 사항

- 모든 시간은 `Asia/Seoul` 기준
- 작업 ID는 고유해야 함
- 서버 재시작 시 코드에 정의된 기본 작업만 복원됨
- 동적으로 추가한 작업은 메모리에만 저장 (재시작 시 사라짐)
