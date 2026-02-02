"""텔레그램 API 유틸리티"""

from typing import Optional

import httpx

from app.config import BOT_TOKEN, WEBHOOK_SECRET


async def send_chat_action(chat_id: int, action: str = "typing") -> bool:
    """타이핑 중 등의 액션 표시"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"chat_id": chat_id, "action": action})
            result = response.json()
            ok = result.get("ok", False)
            if ok:
                print(f"[typing] chat_id={chat_id} 타이핑 표시 성공")
            else:
                print(f"[typing] chat_id={chat_id} 실패: {result}")
            return ok
    except Exception as e:
        print(f"[typing] chat_id={chat_id} 에러: {e}")
        return False


async def send_message(chat_id: int, text: str, parse_mode: str = "Markdown") -> bool:
    """텔레그램으로 메시지 전송"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    async with httpx.AsyncClient() as client:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        response = await client.post(url, json=payload)
        data = response.json()

        if not data.get("ok"):
            # Markdown 파싱 실패시 plain text로 재시도
            if "can't parse" in data.get("description", "").lower():
                payload["parse_mode"] = None
                response = await client.post(url, json=payload)
                data = response.json()

        return data.get("ok", False)


async def set_webhook(webhook_url: str, secret_token: Optional[str] = None) -> bool:
    """텔레그램에 Webhook URL 등록"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"

    payload = {"url": webhook_url}
    if secret_token:
        payload["secret_token"] = secret_token

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        data = response.json()

        if data.get("ok"):
            print(f"Webhook 설정 완료: {webhook_url}")
            if secret_token:
                print("Secret token 설정됨")
            return True
        else:
            print(f"Webhook 설정 실패: {data.get('description')}")
            return False


async def delete_webhook() -> bool:
    """Webhook 삭제 (polling 모드로 전환시 필요)"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"

    async with httpx.AsyncClient() as client:
        response = await client.post(url)
        data = response.json()
        return data.get("ok", False)
