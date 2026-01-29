# User Action Command

사용자가 텔레그램 봇으로 보낸 메시지에 응답한다.

## 실행 순서

1. **메시지 조회**: 봇에 온 새 메시지 확인
   ```bash
   python3 .claude/skills/user-action/scripts/get_bot_messages.py
   ```

2. **메시지 분석**: 사용자 요청 파악

3. **답변 작성**: 요청에 맞는 답변 생성

4. **답변 전송**: 텔레그램으로 전송
   ```bash
   python3 scripts/send_telegram.py "답변 내용"
   ```

5. **읽음 처리**: 처리 완료된 메시지 정리
   ```bash
   python3 .claude/skills/user-action/scripts/get_bot_messages.py --mark-read
   ```

## 답변 가이드라인

- 간결하고 명확하게 답변
- 이모지 적절히 사용
- 한국어로 응답 (사용자가 영어면 영어로)
- 시황 요청시 telegram-collector 스킬 활용
