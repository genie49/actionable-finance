---
description: 텔레그램 봇 메시지에 응답
---

사용자가 텔레그램 봇으로 보낸 메시지에 응답한다.

## 실행 순서

1. **대화 조회**: 봇과의 최근 대화 확인
   ```bash
   uv run python .opencode/skills/user-action/scripts/get_bot_messages.py
   ```

2. **메시지 분석**: 마지막 사용자 메시지 파악

3. **답변 작성**: 요청에 맞는 답변 생성

4. **답변 전송**: 텔레그램으로 전송
   ```bash
   uv run python scripts/send_telegram.py "답변 내용"
   ```

## 답변 가이드라인

- 간결하고 명확하게 답변
- 이모지 적절히 사용
- 한국어로 응답 (사용자가 영어면 영어로)
- 시황 요청시 telegram-collector 스킬 활용
