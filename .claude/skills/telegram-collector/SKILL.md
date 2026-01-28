---
name: telegram-collector
description: |
  텔레그램 그룹/채널에서 메시지를 수집하여 Markdown으로 저장하는 스킬.
  Telethon(User API) 기반으로 동작하며, 지정된 채팅에서 최근 N시간 동안의 메시지를 가져온다.

  사용 시점:
  - "텔레그램 메시지 수집해줘"
  - "텔레그램 그룹에서 최근 대화 가져와"
  - "특정 채널의 24시간 메시지 긁어와"
  - "telegram message collect"
---

# Telegram Message Collector

텔레그램 그룹/채널에서 메시지를 수집하여 Markdown 파일로 저장한다.

## 사전 요구사항

1. **Telethon 설치**
   ```bash
   pip install telethon
   ```

2. **Telegram API 키 발급**
   - https://my.telegram.org 접속
   - "API development tools" 선택
   - App 생성 후 `api_id`와 `api_hash` 획득

3. **환경변수 설정**
   ```bash
   export TELEGRAM_API_ID="your_api_id"
   export TELEGRAM_API_HASH="your_api_hash"
   ```

## 사용법

### 기본 사용 (최근 24시간)

```bash
python scripts/collect_messages.py "@channel_username"
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--hours N` | 수집할 시간 범위 | 24 |
| `--users ID1 ID2` | 특정 사용자만 필터링 | 전체 |
| `--output PATH` | 출력 파일 경로 | ./collected_messages.md |

### 예시

```bash
# 여러 채팅에서 48시간 메시지 수집
python scripts/collect_messages.py "@group1" "@group2" --hours 48

# 특정 사용자 메시지만 필터링
python scripts/collect_messages.py "@mygroup" --users 123456789 987654321

# 출력 경로 지정
python scripts/collect_messages.py "@channel" -o ./reports/telegram_$(date +%Y%m%d).md
```

## 채팅 식별자

다음 형식으로 채팅을 지정할 수 있다:
- Username: `@channel_name` 또는 `channel_name`
- Chat ID: `-1001234567890`
- Invite link: `https://t.me/joinchat/XXXXX`

## 출력 형식

```markdown
# 채널명 메시지 수집

- 수집 시간: 2024-01-15 14:30:00
- 기간: 최근 24시간
- 총 메시지: 150개

---

## 2024-01-15

**[09:30] 홍길동 (@hong):** 안녕하세요

**[10:15] 김철수:**
> 멀티라인
> 메시지입니다
```

## 첫 실행 시

최초 실행 시 Telegram 로그인이 필요하다. 전화번호와 인증 코드를 입력하면 세션이 저장되어 이후에는 자동 로그인된다.

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| `FloodWaitError` | 요청 제한 초과. 잠시 후 재시도 |
| `ChatAdminRequiredError` | 해당 채팅에 접근 권한 없음 |
| 메시지가 비어있음 | 채팅 식별자 확인, 권한 확인 |
