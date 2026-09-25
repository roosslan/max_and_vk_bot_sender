import io
import sys
from datetime import datetime

import requests

VK_API_VERSION = "5.199"
VK_API_METHOD = "https://api.vk.com/method/{method}"


def send_to_vk(token: str, peer_ids: list[str], png_bytes: bytes, filename: str) -> None:
    """Отправляет скриншот от имени сообщества каждому получателю как документ."""
    for peer_id in peer_ids:
        try:
            # Загружаем как документ через docs API
            try:
                resp = requests.get(
                    VK_API_METHOD.format(method="docs.getMessagesUploadServer"),
                    params={"access_token": token, "v": VK_API_VERSION, "peer_id": peer_id},
                    timeout=30,
                )
                resp.raise_for_status()
                upload = resp.json()
                if "error" in upload:
                    raise RuntimeError(f"VK API error: {upload['error']}")
                upload_url = upload["response"]["upload_url"]
                print(f"[DEBUG] Got docs upload URL: {upload_url}", file=sys.stderr)
            except Exception as exc:
                raise RuntimeError(f"Failed to get upload URL: {exc}") from exc

            # Загружаем файл
            try:
                resp = requests.post(
                    upload_url,
                    files={"file": (filename, io.BytesIO(png_bytes))},
                    timeout=30,
                )
                resp.raise_for_status()
                uploaded = resp.json()
                print(f"[DEBUG] Docs upload response: {uploaded}", file=sys.stderr)
                if "error" in uploaded:
                    raise RuntimeError(f"Upload error: {uploaded['error']}")
            except Exception as exc:
                raise RuntimeError(f"Failed to upload doc: {exc}") from exc

            # Сохраняем документ
            try:
                saved = requests.post(
                    VK_API_METHOD.format(method="docs.save"),
                    data={
                        "access_token": token,
                        "v": VK_API_VERSION,
                        "file": uploaded.get("file", ""),
                        "title": filename,
                    },
                    timeout=30,
                ).json()
                if "error" in saved:
                    raise RuntimeError(f"VK API error: {saved['error']}")
                print(f"[DEBUG] Saved doc response: {saved}", file=sys.stderr)

                # docs.save может вернуть {'response': {'type': 'doc', 'doc': {...}}}
                # или {'response': [{'id': ..., 'owner_id': ...}]}
                response = saved.get("response", {})
                if isinstance(response, dict) and "doc" in response:
                    doc = response["doc"]
                elif isinstance(response, list) and len(response) > 0:
                    doc = response[0]
                else:
                    raise RuntimeError(f"Unexpected docs.save response format: {saved}")

                attachment = f"doc{doc['owner_id']}_{doc['id']}"
            except Exception as exc:
                raise RuntimeError(f"Failed to save doc: {exc}") from exc

            # Отправляем сообщение с документом
            resp = requests.post(
                VK_API_METHOD.format(method="messages.send"),
                data={
                    "access_token": token,
                    "v": VK_API_VERSION,
                    "peer_id": peer_id,
                    "random_id": 0,
                    "attachment": attachment,
                },
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            print(f"[DEBUG] Message send response: {result}", file=sys.stderr)
            if "error" in result:
                raise RuntimeError(f"VK API error: {result['error']}")
            print(f"[SUCCESS] Screenshot sent to VK peer {peer_id}", file=sys.stderr)
        except Exception as exc:
            print(f"[ERROR] Failed to send to VK peer {peer_id}: {exc}", file=sys.stderr)
            continue
