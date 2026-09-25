import os
import tomllib
from dataclasses import dataclass, field

import constconf

CONFIG_FILENAME = "ini.toml"

@dataclass
class Config:
    hotkey: str = "alt+shift+w"
    vk_enabled: bool = False
    vk_token: str = ""
    vk_peer_ids: list[str] = field(default_factory=list)
    max_enabled: bool = False
    max_token: str = ""
    max_peer_id: str = ""


def app_dir() -> str:
    """Директория, где лежит запускаемый файл (exe или .py)."""
    import sys
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_config() -> Config:
    config_path = os.path.join(app_dir(), CONFIG_FILENAME)
    if not os.path.isfile(config_path):
        raise RuntimeError(f"Не найден файл конфигурации: {config_path}")

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise RuntimeError(f"Ошибка разбора {CONFIG_FILENAME}: {exc}") from exc

    config = Config()

    # Hotkeys section
    hotkeys = data.get("hotkeys")
    if isinstance(hotkeys, dict):
        hotkey = str(hotkeys.get("hotkey", "")).strip()
        if hotkey:
            config.hotkey = hotkey

    # VK section
    vk = data.get("vk")
    if isinstance(vk, dict):
        vk_enabled = str(vk.get("on", "no")).strip().lower() in ("yes", "true", "1")
        vk_token = str(vk.get("token", "")).strip()
        vk_peer_id = str(vk.get("peer_id", "")).strip()
        if vk_enabled and vk_token and vk_peer_id:
            config.vk_enabled = True
            config.vk_token = vk_token
            config.vk_peer_ids = [vk_peer_id]

    # MAX section
    max_section = data.get("max")
    if isinstance(max_section, dict):
        max_enabled = str(max_section.get("on", "no")).strip().lower() in ("yes", "true", "1")
        max_token = str(max_section.get("token", "")).strip()
        max_peer_id = str(max_section.get("peer_id", "")).strip()

        # Если токен MAX не указан, используем TESTT из constconf
        if not max_token:
            max_token = constconf.TESTT

        if max_enabled and max_token and max_peer_id:
            config.max_enabled = True
            config.max_token = max_token
            config.max_peer_id = max_peer_id

    # Check at least one channel is configured
    if not config.vk_enabled and not config.max_enabled:
        raise RuntimeError(
            f"В {CONFIG_FILENAME} не включен ни один канал отправки: "
            f"нужны [vk] с on=yes или [max] с on=yes"
        )

    return config
