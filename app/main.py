"""FastAPI 애플리케이션 엔트리포인트"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import scheduler
from app.handlers import router as webhook_router
from app.scheduler import router as scheduler_router
from app.config import BOT_TOKEN


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 이벤트"""
    # 시작
    scheduler.start()
    yield
    # 종료
    scheduler.shutdown()


# FastAPI 앱
app = FastAPI(
    title="Actionable Finance",
    description="텔레그램 봇 + 스케줄러",
    lifespan=lifespan,
)

# 라우터 등록
app.include_router(webhook_router)      # /webhook
app.include_router(scheduler_router)    # /scheduler/*


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "ok",
        "bot_token_set": bool(BOT_TOKEN),
    }


# CLI 실행용
if __name__ == "__main__":
    import argparse
    import asyncio
    import uvicorn

    from app.telegram import set_webhook, delete_webhook
    from app.config import WEBHOOK_SECRET

    parser = argparse.ArgumentParser(description="Actionable Finance Server")
    parser.add_argument("--host", default="127.0.0.1", help="호스트 (기본: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="포트 (기본: 8000)")
    parser.add_argument("--webhook-url", help="Webhook URL 설정")
    parser.add_argument("--delete-webhook", action="store_true", help="Webhook 삭제")
    args = parser.parse_args()

    # Webhook 삭제 모드
    if args.delete_webhook:
        asyncio.run(delete_webhook())
        print("Webhook 삭제 완료")
    # Webhook 설정 모드
    elif args.webhook_url:
        webhook_url = args.webhook_url
        if not webhook_url.endswith("/webhook"):
            webhook_url = webhook_url.rstrip("/") + "/webhook"
        asyncio.run(set_webhook(webhook_url, WEBHOOK_SECRET))
    # 서버 실행
    else:
        print(f"\n서버 시작: http://{args.host}:{args.port}")
        print("Webhook: /webhook")
        print("Scheduler: /scheduler/*")
        print("Health: /health")
        print("\nCtrl+C로 종료\n")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
