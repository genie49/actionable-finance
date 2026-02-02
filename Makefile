.PHONY: install server tunnel webhook webhook-delete send collect ask help \
        docker-build docker-up docker-down docker-clean docker-logs

# 기본 포트
PORT ?= 8000

help:
	@echo "사용 가능한 명령어:"
	@echo ""
	@echo "  make install        - uv로 의존성 설치"
	@echo "  make server         - 웹훅 서버 실행 (로컬)"
	@echo "  make tunnel         - Cloudflare Quick Tunnel 실행"
	@echo "  make webhook URL=   - 웹훅 URL 등록"
	@echo "  make webhook-delete - 웹훅 삭제"
	@echo "  make send MSG=      - 메시지 전송"
	@echo "  make collect        - 봇 메시지 조회"
	@echo "  make ask Q=         - AI에게 질문"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - Docker 이미지 빌드"
	@echo "  make docker-up      - Docker 컨테이너 실행"
	@echo "  make docker-down    - Docker 컨테이너 중지"
	@echo "  make docker-clean   - Docker 정리 (컨테이너 + 이미지)"
	@echo "  make docker-logs    - Docker 로그 확인"
	@echo ""
	@echo "예시:"
	@echo "  make webhook URL=https://xxx.trycloudflare.com"
	@echo "  make send MSG='안녕하세요'"
	@echo "  make ask Q='너는 누구'"

# uv 환경 설치
install:
	uv sync

# 웹훅 서버 실행 (로컬 모드)
server:
	uv run python -m app.main --host 0.0.0.0 --port $(PORT)

# Cloudflare Quick Tunnel 실행
tunnel:
	cloudflared tunnel --url http://localhost:$(PORT)

# 웹훅 URL 등록
webhook:
ifndef URL
	$(error URL이 필요합니다. 예: make webhook URL=https://xxx.trycloudflare.com)
endif
	uv run python -m app.main --webhook-url $(URL)/webhook

# 웹훅 삭제
webhook-delete:
	uv run python -m app.main --delete-webhook

# 메시지 전송
send:
ifndef MSG
	$(error MSG가 필요합니다. 예: make send MSG='안녕하세요')
endif
	uv run python scripts/send_telegram.py "$(MSG)"

# 봇 대화 히스토리 조회
collect:
	uv run python .opencode/skills/user-action/scripts/get_bot_messages.py

# AI에게 질문
ask:
ifndef Q
	$(error Q가 필요합니다. 예: make ask Q='너는 누구')
endif
	opencode run "$(Q)" -m "zai-coding-plan/glm-4.7"

# ===== Docker =====

# Docker 이미지 빌드
docker-build:
	docker-compose build

# Docker 컨테이너 실행
docker-up:
	docker-compose up -d

# Docker 컨테이너 중지
docker-down:
	docker-compose down

# Docker 정리 (컨테이너 + 이미지)
docker-clean:
	docker-compose down --rmi local --volumes --remove-orphans

# Docker 로그 확인
docker-logs:
	docker-compose logs -f
