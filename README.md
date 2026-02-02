# Actionable Finance

텔레그램 봇 + AI 에이전트 기반 금융 정보 자동화 도구.

## 주요 기능

- **Telegram Webhook 서버**: 메시지 수신 시 AI가 자동 응답
- **메시지 수집**: 텔레그램 그룹/채널에서 메시지 수집 및 요약
- **Upbit 트레이딩**: 암호화폐 포지션 분석 및 리포트
- **Docker + Cloudflare Tunnel**: 24시간 서버 운영

## 빠른 시작

### 1. 의존성 설치

```bash
# uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
make install
# 또는
uv sync
```

### 2. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일 수정:

```bash
# Telegram API (https://my.telegram.org/apps)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890

# Telegram Bot (@BotFather에서 발급)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHI...
TELEGRAM_CHAT_ID=  # get_chat_id.py로 확인

# Cloudflare Tunnel (Zero Trust에서 생성)
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoi...
```

### 3. Telegram 세션 생성 (최초 1회)

```bash
python scripts/generate_session.py
```

### 4. Docker로 실행

```bash
make docker-build   # 이미지 빌드
make docker-up      # 컨테이너 실행
make docker-logs    # 로그 확인
```

## Makefile 명령어

```bash
# 기본
make install        # uv로 의존성 설치
make server         # 웹훅 서버 로컬 실행
make tunnel         # Cloudflare Quick Tunnel

# Webhook
make webhook URL=https://webhook.example.com  # Webhook URL 등록
make webhook-delete                            # Webhook 삭제

# 메시지
make send MSG='안녕하세요'  # 텔레그램 메시지 전송
make collect               # 봇 대화 히스토리 조회

# Docker
make docker-build   # 이미지 빌드
make docker-up      # 컨테이너 실행
make docker-down    # 컨테이너 중지
make docker-clean   # 정리 (이미지 + 볼륨)
make docker-logs    # 로그 확인
```

## 프로젝트 구조

```
.
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── .env                          # 환경변수 (gitignore)
├── .env.example
├── telegram-targets.json         # 수집 대상 설정
├── opencode.jsonc                # OpenCode 설정
├── AGENTS.md                     # AI 에이전트 가이드
│
├── scripts/
│   ├── telegram_webhook.py       # Webhook 서버 (FastAPI)
│   ├── send_telegram.py          # 메시지 전송
│   ├── get_chat_id.py            # Chat ID 확인
│   └── generate_session.py       # 세션 생성
│
└── .opencode/skills/
    ├── daily-summary/            # 일일 요약 생성
    ├── telegram-collector/       # 메시지 수집
    ├── upbit-trading/            # 업비트 트레이딩
    └── user-action/              # 사용자 메시지 응답
```

## Cloudflare Tunnel 설정

1. [Cloudflare Zero Trust](https://one.dash.cloudflare.com/) 접속
2. **Networks** → **Tunnels** → **Create a tunnel**
3. 터널 이름 지정, 토큰 복사
4. Public Hostname 설정:
   - Subdomain: `webhook`
   - Domain: 본인 도메인
   - Type: `HTTP`
   - URL: `webhook:8000`
5. `.env`에 토큰 추가:
   ```
   CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoi...
   ```

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| `SessionPasswordNeededError` | 2단계 인증 비밀번호 입력 필요 |
| `FloodWaitError` | API 요청 제한. 잠시 후 재시도 |
| `ChatAdminRequiredError` | 해당 채팅에 접근 권한 없음 |
| Typing 표시 안 보임 | Telegram 데스크톱 제한. 모바일에서 확인 |
| OpenCode 실행 실패 | Docker 내 opencode 설치 확인 |
