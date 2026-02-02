---
description: 24시간 텔레그램 메시지 요약 전송
agent: daily-summary
---

24시간 동안 수집된 텔레그램 메시지를 요약하여 사용자에게 전송한다.

메시지 수집 → 요약 생성 → 텔레그램 전송 순서로 진행한다.

## 실행 순서

1. **메시지 수집**: 최근 24시간 메시지 수집
   ```bash
   uv run python .opencode/skills/telegram-collector/scripts/collect_messages.py --hours 24 -o collected_messages/$(date +%Y-%m-%d).md
   ```

2. **수집 파일 확인**
   ```bash
   ls -la collected_messages/
   ```

3. **메시지 읽기**: 오늘 날짜 파일 또는 최신 파일 읽기
   - 파일 위치: `collected_messages/YYYY-MM-DD.md`
   - 파일이 크면 Grep으로 주요 키워드 검색

4. **요약 생성**: 카테고리별로 핵심 내용 요약
   - 시장 동향: 주요 지수, 가격 변동
   - 주요 뉴스: 중요 이슈, 정책 변화
   - 투자 정보: 실적, 수주, 공시
   - 액션 아이템: 주의할 사항, 기회

5. **텔레그램 전송**
   ```bash
   uv run python scripts/send_telegram.py "요약 내용"
   ```

## 요약 형식

```
📊 24시간 시황 요약 (MM/DD HH:MM 기준)

📈 시장 동향
• 핵심 내용 1
• 핵심 내용 2

📰 주요 뉴스
• 뉴스 1
• 뉴스 2

💼 투자 정보
• 정보 1
• 정보 2

⚠️ 주의 사항
• 사항 1

---
총 N개 메시지 중 주요 내용 요약
```

## 가이드라인

- 전체 길이: 2000자 이내
- 중요도 순 정렬
- 한국어로 작성
- 수집된 메시지가 없으면 알림
