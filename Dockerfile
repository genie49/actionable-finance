FROM python:3.12-slim

WORKDIR /app

# 필수 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# opencode 설치
RUN curl -fsSL https://opencode.ai/install | bash \
    && find /root -name "opencode" -type f -executable -exec mv {} /usr/local/bin/ \;

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 의존성 파일 복사 및 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 소스 복사
COPY scripts/ ./scripts/
COPY .opencode/ ./.opencode/
COPY opencode.jsonc.template ./
COPY telegram-targets.json ./
COPY AGENTS.md ./

# entrypoint 실행 권한
RUN chmod +x /app/scripts/entrypoint.sh

# 환경변수
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# entrypoint로 실행 (환경변수에서 config 생성 후 서버 시작)
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
