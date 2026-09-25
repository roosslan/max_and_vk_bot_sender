import io
import sys
import threading
from datetime import datetime

import keyboard
import mss
import mss.tools
from PIL import ImageGrab

from config import load_config
from max_sender import send_to_max
from vk_sender import send_to_vk

APP_NAME = "max_and_vk_bot_sender"


def grab_full_screen_png() -> bytes:
    """Скриншот всех мониторов сразу, в виде PNG-байтов.

    Сначала пробует mss, потом PIL.ImageGrab как fallback.
    """
    try:
        # Первый способ: mss (обычно быстрее и надёжнее)
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            shot = sct.grab(monitor)
            return mss.tools.to_png(shot.rgb, shot.size)
    except Exception as mss_error:
        try:
            # Fallback: PIL.ImageGrab (работает когда mss блокируется)
            img = ImageGrab.grab()
            png_buffer = io.BytesIO()
            img.save(png_buffer, format="PNG")
            return png_buffer.getvalue()
        except Exception as pil_error:
            # Обе попытки неудачны
            raise RuntimeError(
                f"Failed to capture screen: mss ({mss_error}), "
                f"PIL.ImageGrab ({pil_error})"
            )


def send_screenshot(config) -> None:
    try:
        png_bytes = grab_full_screen_png()
    except Exception:
        # Тихо игнорируем — без логов и уведомлений.
        return

    filename = f"screenshot_{datetime.now():%Y%m%d_%H%M%S}.png"

    # MAX отправляется первым
    if config.max_enabled:
        send_to_max(config.max_token, config.max_peer_id, png_bytes, filename)

    # Потом VK
    if config.vk_enabled:
        send_to_vk(config.vk_token, config.vk_peer_ids, png_bytes, filename)


def main() -> None:
    try:
        config = load_config()
    except RuntimeError:
        sys.exit(1)

    # Отправка в отдельном потоке, чтобы сеть не блокировала обработку клавиш.
    keyboard.add_hotkey(
        config.hotkey,
        lambda: threading.Thread(
            target=send_screenshot, args=(config,), daemon=True
        ).start(),
    )

    # Слушаем хоткеи до Ctrl+C
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
