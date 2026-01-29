# Actionable Finance

텔레그램 그룹/채널에서 메시지를 수집하여 분석하는 도구.

## 설정

### 1. 의존성 설치

```bash
pip install telethon python-dotenv
```

### 2. Telegram API 키 발급

1. https://my.telegram.org 접속
2. 로그인 후 "API development tools" 선택
3. App 생성:
   - App title: `Message Collector` (아무 이름)
   - Short name: `msgcollector` (5-32자, 영숫자)
   - Platform: `Desktop`
4. `api_id`와 `api_hash` 복사

### 3. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일에 API 키 입력:

```
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
```

### 4. 세션 생성 (최초 1회)

```bash
python scripts/generate_session.py
```

- 전화번호 입력 (국가코드 포함: +821012345678)
- Telegram 앱에서 받은 인증코드 입력
- 세션 문자열이 자동으로 `.env`에 저장됨

### 5. 수집 대상 설정

```bash
python .claude/skills/telegram-collector/scripts/setup_targets.py
```

대화형으로 그룹/채널 선택 후 `telegram-targets.json`에 저장됨.

## 사용법

### 설정된 대상에서 메시지 수집

```bash
python .claude/skills/telegram-collector/scripts/collect_messages.py
```

### 옵션

```bash
# 최근 48시간
python .claude/skills/telegram-collector/scripts/collect_messages.py --hours 48

# 특정 채널만
python .claude/skills/telegram-collector/scripts/collect_messages.py @channel_name

# 출력 경로 지정
python .claude/skills/telegram-collector/scripts/collect_messages.py -o ./reports/messages.md
```

## 파일 구조

```
.
├── .env                          # API 키 + 세션 (gitignore)
├── .env.example                  # 환경변수 예시
├── telegram-targets.json         # 수집 대상 설정 (gitignore)
├── telegram-targets.example.json
├── scripts/
│   └── generate_session.py       # 세션 생성 (최초 1회)
└── .claude/skills/telegram-collector/
    ├── SKILL.md
    └── scripts/
        ├── collect_messages.py   # 메시지 수집
        └── setup_targets.py      # 대상 설정 헬퍼
```

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| `SessionPasswordNeededError` | 2단계 인증 비밀번호 입력 필요 |
| `FloodWaitError` | API 요청 제한. 잠시 후 재시도 |
| `ChatAdminRequiredError` | 해당 채팅에 접근 권한 없음 |
