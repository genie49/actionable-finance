#!/bin/bash
set -e

# opencode.jsonc 생성 (환경변수에서 API 키 주입)
if [ -n "$ZAI_API_KEY" ]; then
    sed "s|\${ZAI_API_KEY}|$ZAI_API_KEY|g" /app/opencode.jsonc.template > /app/opencode.jsonc
    echo "opencode.jsonc generated with API key"
else
    echo "WARNING: ZAI_API_KEY not set, opencode may not work"
fi

# Cloudflare Tunnel 시작 (백그라운드)
if [ -n "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
    echo "Starting Cloudflare Tunnel..."
    cloudflared tunnel --no-autoupdate run --token "$CLOUDFLARE_TUNNEL_TOKEN" &
    CLOUDFLARED_PID=$!
    echo "Cloudflare Tunnel started (PID: $CLOUDFLARED_PID)"
else
    echo "WARNING: CLOUDFLARE_TUNNEL_TOKEN not set, tunnel disabled"
fi

# 종료 시그널 핸들링
cleanup() {
    echo "Shutting down..."
    if [ -n "$CLOUDFLARED_PID" ]; then
        kill $CLOUDFLARED_PID 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGTERM SIGINT

# 웹서버 실행 (localhost만 - 외부 직접 접근 차단)
# Cloudflare Tunnel이 localhost:8000으로 트래픽 전달
echo "Starting uvicorn on localhost:8000 (internal only)..."
exec uv run uvicorn scripts.telegram_webhook:app --host 127.0.0.1 --port 8000
