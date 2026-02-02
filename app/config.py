"""환경변수 및 설정 관리"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def find_project_root() -> Path:
    """프로젝트 루트 디렉토리 찾기"""
    current = Path(__file__).resolve().parent.parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()


# 프로젝트 루트
PROJECT_ROOT = find_project_root()

# 환경변수 로드
load_dotenv(PROJECT_ROOT / ".env")

# Telegram 설정
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET")

# API 키
ZAI_API_KEY = os.environ.get("ZAI_API_KEY")

# 타임존
TIMEZONE = "Asia/Seoul"

# 검증
if not BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN이 필요합니다.")
    sys.exit(1)
