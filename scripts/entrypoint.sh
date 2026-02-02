#!/bin/bash
set -e

# opencode.jsonc 생성 (환경변수에서 API 키 주입)
if [ -n "$ZAI_API_KEY" ]; then
    sed "s|\${ZAI_API_KEY}|$ZAI_API_KEY|g" /app/opencode.jsonc.template > /app/opencode.jsonc
    echo "opencode.jsonc generated with API key"
else
    echo "WARNING: ZAI_API_KEY not set, opencode may not work"
fi

# 서버 실행 (Railway는 PORT 환경변수 제공)
exec uv run uvicorn scripts.telegram_webhook:app --host 0.0.0.0 --port ${PORT:-8000}
