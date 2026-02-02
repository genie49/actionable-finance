---
name: user-action
description: |
  사용자가 텔레그램 봇으로 보낸 메시지에 응답하는 스킬.
  /user-action 커맨드로 실행되며, 봇과의 대화 히스토리를 읽고 텔레그램으로 답변을 전송한다.
---

# User Action

텔레그램 봇을 통해 사용자와 대화하는 스킬.

## 실행 방법

`/user-action` 커맨드 실행

## 워크플로우

1. 봇과의 최근 대화 조회
2. 메시지 내용 분석
3. 적절한 답변 생성
4. 텔레그램으로 답변 전송

## 스크립트

### 대화 히스토리 조회

```bash
uv run python .opencode/skills/user-action/scripts/get_bot_messages.py
```

옵션:
- `--limit N`, `-n N`: 조회할 메시지 수 (기본: 10)
- `--json`: JSON 형식 출력

### 답변 전송

```bash
uv run python scripts/send_telegram.py "답변 내용"
```

## 실행 순서

1. `get_bot_messages.py`로 최근 대화 확인
2. 마지막 사용자 메시지를 분석하고 답변 작성
3. `send_telegram.py`로 답변 전송
