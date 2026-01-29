---
name: user-action
description: |
  사용자가 텔레그램 봇으로 보낸 메시지에 응답하는 스킬.
  /user-action 커맨드로 실행되며, 봇에 온 메시지를 읽고 텔레그램으로 답변을 전송한다.
---

# User Action

텔레그램 봇을 통해 사용자와 대화하는 스킬.

## 실행 방법

`/user-action` 커맨드 실행

## 워크플로우

1. 봇에 온 메시지 조회
2. 메시지 내용 분석
3. 적절한 답변 생성
4. 텔레그램으로 답변 전송
5. 메시지 읽음 처리

## 스크립트

### 메시지 조회

```bash
python3 .claude/skills/user-action/scripts/get_bot_messages.py
```

옵션:
- `--limit N`: 최근 N개 메시지 조회 (기본: 10)
- `--mark-read`: 조회 후 읽음 처리
- `--json`: JSON 형식 출력

### 답변 전송

```bash
python3 scripts/send_telegram.py "답변 내용"
```

## 실행 순서

1. `get_bot_messages.py`로 새 메시지 확인
2. 메시지 내용을 분석하고 답변 작성
3. `send_telegram.py`로 답변 전송
4. `get_bot_messages.py --mark-read`로 읽음 처리
