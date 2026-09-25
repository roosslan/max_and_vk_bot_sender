import io
import sys
import threading
import urllib3
from datetime import datetime

import requests

# Отключаем предупреждения о проверке SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def send_to_max(token: str, peer_id: str, png_bytes: bytes, filename: str) -> None:
    """Отправляет скриншот в Mail.ru MAX диалог."""
    try:
        headers = {
            "Authorization": token,
        }

        # Шаг 1: запрос URL для загрузки
        print("[DEBUG] Requesting MAX upload URL...", file=sys.stderr)
        resp = requests.post(
            "https://platform-api2.max.ru/uploads",
            params={"type": "image"},
            headers=headers,
            timeout=30,
            verify=False,
        )
        resp.raise_for_status()
        upload_info = resp.json()
        print(f"[DEBUG] MAX upload info response: {upload_info}", file=sys.stderr)

        upload_url = upload_info.get("url")
        if not upload_url:
            raise RuntimeError(f"No upload URL in response: {upload_info}")

        # Шаг 2: загрузка файла на полученный URL
        print(f"[DEBUG] Uploading to: {upload_url}", file=sys.stderr)
        upload_resp = requests.post(
            upload_url,
            files={"data": (filename, io.BytesIO(png_bytes), "image/png")},
            timeout=30,
            verify=False,
        )
        upload_resp.raise_for_status()
        upload_result = upload_resp.json()
        print(f"[DEBUG] MAX file upload response: {upload_result}", file=sys.stderr)

        # Токен может быть в photos[photoId]['token']
        media_token = upload_result.get("token")
        if not media_token and "photos" in upload_result:
            # Берём первый (и единственный) токен из photos
            for photo_id, photo_data in upload_result["photos"].items():
                media_token = photo_data.get("token")
                if media_token:
                    break

        if not media_token:
            raise RuntimeError(f"No token in upload response: {upload_result}")

        print(f"[DEBUG] Got media token: {media_token[:20]}...", file=sys.stderr)

        # Пауза для обработки файла на сервере
        print("[DEBUG] Waiting 3 seconds for server to process file...", file=sys.stderr)
        threading.Event().wait(3)

        # Шаг 3: отправка сообщения с вложением
        payload = {
            "text": f"Screenshot {datetime.now():%Y-%m-%d %H:%M:%S}",
            "attachments": [
                {
                    "type": "image",
                    "payload": {"token": media_token},
                }
            ],
        }

        print("[DEBUG] Sending message with image attachment...", file=sys.stderr)
        resp = requests.post(
            "https://platform-api2.max.ru/messages",
            params={"user_id": peer_id},
            headers={**headers, "Content-Type": "application/json"},
            json=payload,
            timeout=30,
            verify=False,
        )
        resp.raise_for_status()
        result = resp.json()
        print(f"[DEBUG] MAX send response: {result}", file=sys.stderr)

        print(f"[SUCCESS] Screenshot sent to MAX peer {peer_id}", file=sys.stderr)
    except Exception as exc:
        print(f"[ERROR] Failed to send to MAX peer {peer_id}: {exc}", file=sys.stderr)
