import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, REPOSITORY_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class InlineKeyboardButton:
    def __init__(self, text, callback_data):
        self.text = text
        self.callback_data = callback_data


class ImageQueueTestCase(unittest.TestCase):
    def test_constructor_preserves_queue_metadata(self):
        module = load_module("image_queue_under_test", "convert/ImageQueue.py")

        queue_item = module.ImageQueue(11, 22, 33, pending=True, downloaded=False)

        self.assertEqual(11, queue_item.chat_id)
        self.assertEqual(22, queue_item.message_id)
        self.assertEqual(33, queue_item.image_id)
        self.assertTrue(queue_item.pending)
        self.assertFalse(queue_item.downloaded)


class BackblazeConfigTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        package = types.ModuleType("config_under_test")
        package.__path__ = []
        sys.modules[package.__name__] = package
        load_module("config_under_test.base_config", "configs/base_config.py")
        cls.module = load_module(
            "config_under_test.backblaze_config",
            "configs/backblaze_config.py",
        )

    def test_defaults_and_missing_values_are_reported(self):
        config = self.module.BackblazeConfig()

        self.assertEqual("BackBlaze", config.description)
        self.assertEqual("img_bed", config.what)
        self.assertEqual("bot-images/", config.base_path)
        self.assertIn("app_key_id: 未配置", config.get_conf_brief())
        self.assertIn("公网访问链接: 未配置", config.get_conf_brief())

    def test_access_url_is_normalized_and_values_are_summarized(self):
        config = self.module.BackblazeConfig(
            application_key_id="key-id",
            application_key="12345678901",
            bucket_name="images",
            access_url_base="https://cdn.example.com",
        )

        self.assertEqual("https://cdn.example.com/", config.access_url_base)
        summary = config.get_conf_brief()
        self.assertIn("app_key_id: key-id", summary)
        self.assertIn("app_key: 12345**********7890", summary)
        self.assertIn("存储桶名称: images", summary)
        self.assertIn("公网访问链接: https://cdn.example.com/", summary)

    def test_existing_access_url_slash_is_not_duplicated(self):
        config = self.module.BackblazeConfig(
            access_url_base="https://cdn.example.com/",
        )

        self.assertEqual("https://cdn.example.com/", config.access_url_base)


class FileInfoTestCase(unittest.TestCase):
    def test_get_size_returns_kibibytes(self):
        database = types.ModuleType("database")
        database.ImageInfo = object
        database.database = object()
        with patch.dict(sys.modules, {"database": database}):
            module = load_module("get_info_under_test", "images/get_info.py")

        with tempfile.NamedTemporaryFile() as temporary_file:
            temporary_file.write(b"x" * 1536)
            temporary_file.flush()
            self.assertEqual(1.5, module.get_size(temporary_file.name))


class KeyboardTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        telegram = types.ModuleType("telegram")
        telegram.InlineKeyboardButton = InlineKeyboardButton
        with patch.dict(sys.modules, {"telegram": telegram}):
            cls.handlers = load_module(
                "handler_keyboard_under_test",
                "handlers/generate_inline_keyboard.py",
            )
            cls.configs = load_module(
                "config_keyboard_under_test",
                "configs/generate_inline_keyboard.py",
            )

    def assert_callback(self, keyboard, expected):
        self.assertEqual(expected, json.loads(keyboard[0][0].callback_data))

    def test_origin_failure_keyboard_supports_retry_options(self):
        no_retry = self.handlers.get_origin_fail_keyboard(42)
        retry = self.handlers.get_origin_fail_keyboard(42, reason="retry", no_retry=False)

        self.assertEqual("获取原图出错！", no_retry[0][0].text)
        self.assert_callback(no_retry, {"op": "gtfnt", "cid": 42})
        self.assertEqual("retry", retry[0][0].text)
        self.assert_callback(retry, {"op": "gtf", "cid": 42})

    def test_origin_status_keyboards_have_expected_operations(self):
        cases = (
            (self.handlers.already_get_origin_keyboard, "agto"),
            (self.handlers.sending_origin_keyboard, "agto"),
            (self.handlers.getting_origin_keyboard, "gito"),
            (self.handlers.timeout_keyboard, "timeout"),
        )
        for factory, operation in cases:
            with self.subTest(factory=factory.__name__):
                self.assert_callback(factory(), {"op": operation})

        self.assert_callback(
            self.handlers.get_origin_keyboard(99),
            {"op": "gto", "cid": 99},
        )

    def test_configuration_keyboards_expose_expected_actions(self):
        change_callbacks = [
            button.callback_data
            for row in self.configs.config_img_bed_change_keyboard()
            for button in row
        ]
        self.assertEqual(
            [
                "config:image_bed",
                "config:image_bed:cancel",
                "config:image_bed:set:backblaze",
            ],
            change_callbacks,
        )

        edit_callbacks = [
            button.callback_data
            for row in self.configs.config_img_bed_backblaze_edit_keyboard()
            for button in row
        ]
        self.assertIn("config:image_bed:edit:app_key_id", edit_callbacks)
        self.assertIn("config:image_bed:edit:base_path", edit_callbacks)
        self.assertEqual({"op": "empty"}, json.loads(edit_callbacks[-1]))

        self.assertEqual(
            "config:image_bed:change",
            self.configs.config_img_bed_none_edit_keyboard()[0][0].callback_data,
        )
        self.assertEqual(
            "config:image_bed",
            self.configs.config_main_menu_keyboard()[0][0].callback_data,
        )


if __name__ == "__main__":
    unittest.main()
