import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import config
import max_sender
import vk_sender


class LoadConfigTests(unittest.TestCase):
    def test_loads_vk_config(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "ini.toml").write_text(
                '[vk]\non = "yes"\ntoken = "vk1.a.token"\npeer_id = "111"\n',
                encoding="utf-8",
            )
            with patch.object(config, "app_dir", return_value=directory):
                cfg = config.load_config()
        self.assertEqual(cfg.vk_enabled, True)
        self.assertEqual(cfg.vk_token, "vk1.a.token")
        self.assertEqual(cfg.vk_peer_ids, ["111"])
        self.assertEqual(cfg.max_enabled, False)

    def test_loads_max_config(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "ini.toml").write_text(
                '[max]\non = "yes"\ntoken = "max-token"\npeer_id = "111"\n',
                encoding="utf-8",
            )
            with patch.object(config, "app_dir", return_value=directory):
                cfg = config.load_config()
        self.assertEqual(cfg.max_enabled, True)
        self.assertEqual(cfg.max_token, "max-token")
        self.assertEqual(cfg.max_peer_id, "111")
        self.assertEqual(cfg.vk_enabled, False)

    def test_loads_both_vk_and_max(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "ini.toml").write_text(
                '[vk]\non = "yes"\ntoken = "vk1.a.token"\npeer_id = "111"\n\n'
                '[max]\non = "yes"\ntoken = "max-token"\npeer_id = "222"\n',
                encoding="utf-8",
            )
            with patch.object(config, "app_dir", return_value=directory):
                cfg = config.load_config()
        self.assertEqual(cfg.vk_enabled, True)
        self.assertEqual(cfg.vk_token, "vk1.a.token")
        self.assertEqual(cfg.max_enabled, True)
        self.assertEqual(cfg.max_token, "max-token")

    def test_rejects_missing_configuration_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(config, "app_dir", return_value=directory):
                with self.assertRaisesRegex(RuntimeError, "Не найден файл конфигурации"):
                    config.load_config()

    def test_rejects_when_no_channel_configured(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "ini.toml").write_text("# empty\n", encoding="utf-8")
            with patch.object(config, "app_dir", return_value=directory):
                with self.assertRaisesRegex(RuntimeError, "не включен ни один канал"):
                    config.load_config()


class VkSendTests(unittest.TestCase):
    @patch.object(vk_sender.requests, "post")
    @patch.object(vk_sender.requests, "get")
    def test_sends_doc_to_peer(self, get_mock, post_mock):
        get_response = MagicMock()
        get_response.json.return_value = {
            "response": {"upload_url": "https://upload.vk.com/upload"}
        }
        get_mock.return_value = get_response

        upload_response = MagicMock()
        upload_response.json.return_value = {"file": "uploaded_file_data"}

        save_response = MagicMock()
        save_response.json.return_value = {
            "response": [{"owner_id": -123, "id": 456}]
        }

        send_response = MagicMock()
        send_response.json.return_value = {"response": 789}

        post_mock.side_effect = [upload_response, save_response, send_response]

        vk_sender.send_to_vk("vk1.a.token", ["111"], b"png-data", "shot.png")

        self.assertEqual(get_mock.call_count, 1)
        self.assertEqual(post_mock.call_count, 3)


class MaxSendTests(unittest.TestCase):
    @patch.object(max_sender.requests, "post")
    def test_sends_file_to_max(self, post_mock):
        # Первый вызов — POST /uploads?type=image (возвращает upload URL)
        upload_info_response = MagicMock()
        upload_info_response.json.return_value = {"url": "https://upload.server/abc123"}

        # Второй вызов — POST на upload URL (возвращает token)
        file_upload_response = MagicMock()
        file_upload_response.json.return_value = {"token": "media-token-xyz"}

        # Третий вызов — POST /messages (отправка с вложением)
        send_response = MagicMock()
        send_response.json.return_value = {"messageId": 456}

        post_mock.side_effect = [upload_info_response, file_upload_response, send_response]

        max_sender.send_to_max("max-token", "111", b"png-data", "shot.png")

        self.assertEqual(post_mock.call_count, 3)

        # Проверяем первый вызов (GET upload info)
        info_call = post_mock.call_args_list[0]
        self.assertTrue(info_call.args[0].endswith("/uploads"))

        # Проверяем третий вызов (send message)
        send_call = post_mock.call_args_list[2]
        self.assertTrue(send_call.args[0].endswith("/messages"))


if __name__ == "__main__":
    unittest.main()
