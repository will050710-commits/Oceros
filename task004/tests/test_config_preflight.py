import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from task004.config import Config, ConfigError, load_config, parse_config
from task004.preflight import check_preflight, windows_system_commit


class ConfigTests(unittest.TestCase):
    def test_context_is_required(self):
        with self.assertRaises(ConfigError):
            parse_config({})

    def test_defaults_and_round_trip(self):
        config = parse_config({"n_ctx": 512})
        self.assertEqual(config.runtime, "mock")
        self.assertFalse(config.thinking)
        self.assertEqual(parse_config(config.to_dict()), config)

    def test_direct_constructor_validates(self):
        with self.assertRaises(ConfigError):
            Config(n_ctx=512, runtime="llama.cpp")

    def test_boolean_does_not_count_as_integer(self):
        for key in ("n_ctx", "max_new_tokens", "min_available_ram_bytes", "min_free_disk_bytes"):
            with self.subTest(key=key), self.assertRaises(ConfigError):
                parse_config({"n_ctx": 512, key: True})

    def test_nonpositive_context_rejected(self):
        for value in (0, -1, "512", 1.5, None):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                parse_config({"n_ctx": value})

    def test_non_thinking_enforced(self):
        for value in (True, 0, "false", None):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                parse_config({"n_ctx": 512, "thinking": value})

    def test_token_cap_boundaries(self):
        for value in (1, 95, 96):
            self.assertEqual(parse_config({"n_ctx": 512, "max_new_tokens": value}).max_new_tokens, value)
        for value in (0, 97):
            with self.assertRaises(ConfigError):
                parse_config({"n_ctx": 512, "max_new_tokens": value})

    def test_unknown_keys_and_external_runtime_rejected(self):
        for data in ({"url": "https://example.com"}, {"command": "anything"}, {"runtime": "real"}):
            with self.subTest(data=data), self.assertRaises(ConfigError):
                parse_config({"n_ctx": 512, **data})

    def test_config_must_be_object(self):
        for value in ([], None, True, 1):
            with self.assertRaises(ConfigError):
                parse_config(value)

    def test_timeout_and_interval_validation(self):
        for key in ("timeout_s", "startup_timeout_s", "sample_interval_s"):
            for value in (True, 0, -1, float("nan"), float("inf"), "5", 10 ** 400):
                with self.subTest(key=key, value=str(value)), self.assertRaises(ConfigError):
                    parse_config({"n_ctx": 512, key: value})
        with self.assertRaises(ConfigError):
            parse_config({"n_ctx": 512, "sample_interval_s": 0.009})
        self.assertEqual(Config(n_ctx=512, sample_interval_s=0.01).sample_interval_s, 0.01)

    def test_resource_thresholds_must_be_nonnegative(self):
        for key in ("min_available_ram_bytes", "min_free_disk_bytes"):
            self.assertEqual(getattr(parse_config({"n_ctx": 512, key: 0}), key), 0)
            with self.assertRaises(ConfigError):
                parse_config({"n_ctx": 512, key: -1})

    def test_image_requires_explicit_token_budget(self):
        for data in ({"image_long_edge_px": 768}, {"max_image_tokens": 64}):
            with self.assertRaises(ConfigError):
                parse_config({"n_ctx": 512, **data})

    def test_image_dimension_boundaries(self):
        for size in (1, 767, 768):
            config = Config(n_ctx=512, image_long_edge_px=size, max_image_tokens=64)
            self.assertEqual(config.image_long_edge_px, size)
        for size in (0, 769, 1024, True):
            with self.assertRaises(ConfigError):
                Config(n_ctx=512, image_long_edge_px=size, max_image_tokens=64)
        for tokens in (0, -1, True):
            with self.assertRaises(ConfigError):
                Config(n_ctx=512, image_long_edge_px=768, max_image_tokens=tokens)

    def test_mock_scenario_and_delay(self):
        self.assertEqual(Config(n_ctx=1, mock_scenario="slow", mock_delay_s=0).mock_delay_s, 0)
        for value in (-1, True, float("nan")):
            with self.assertRaises(ConfigError):
                Config(n_ctx=1, mock_delay_s=value)
        with self.assertRaises(ConfigError):
            Config(n_ctx=1, mock_scenario="arbitrary-command")

    def test_json_load_and_reject_duplicate_or_nonfinite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"n_ctx": 512}), encoding="utf-8")
            self.assertEqual(load_config(path).n_ctx, 512)
            for text in ('{"n_ctx":1,"n_ctx":2}', '{"n_ctx":NaN}', '{"n_ctx":Infinity}', '{broken'):
                path.write_text(text, encoding="utf-8")
                with self.subTest(text=text), self.assertRaises(ConfigError):
                    load_config(path)

    def test_invalid_utf8_and_missing_file_are_safe_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            with self.assertRaises(ConfigError):
                load_config(path)
            path.write_bytes(b"\xff")
            with self.assertRaises(ConfigError):
                load_config(path)

    def test_integer_over_python_digit_limit_is_config_error(self):
        import sys

        limit = sys.get_int_max_str_digits()
        if not limit:
            self.skipTest("interpreter integer digit limit is disabled")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"n_ctx":' + ('9' * (limit + 1)) + '}', encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)


class PreflightTests(unittest.TestCase):
    def measure(self, ram, disk, directory):
        config = Config(n_ctx=512, min_available_ram_bytes=100, min_free_disk_bytes=200)
        with patch("task004.preflight.psutil.virtual_memory", return_value=SimpleNamespace(available=ram)), \
             patch("task004.preflight.shutil.disk_usage", return_value=SimpleNamespace(free=disk)):
            return check_preflight(config, Path(directory))

    def test_ram_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(self.measure(99, 200, directory)["ready"])
            self.assertTrue(self.measure(100, 200, directory)["ready"])
            self.assertTrue(self.measure(101, 200, directory)["ready"])

    def test_disk_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(self.measure(100, 199, directory)["ready"])
            self.assertTrue(self.measure(100, 200, directory)["ready"])
            self.assertTrue(self.measure(100, 201, directory)["ready"])

    def test_nested_missing_directory_uses_ancestor_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "nested" / "output"
            self.assertTrue(self.measure(100, 200, target)["ready"])
            self.assertFalse(target.parent.exists())

    def test_existing_file_blocks_output(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "output"
            target.write_text("user data")
            self.assertFalse(self.measure(100, 200, target)["ready"])
            self.assertFalse(self.measure(100, 200, target / "child")["ready"])
            self.assertEqual(target.read_text(), "user data")

    def test_ram_failure_is_not_zero_or_success(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("task004.preflight.psutil.virtual_memory", side_effect=OSError("sensitive content")):
            report = check_preflight(Config(n_ctx=1), Path(directory))
            self.assertFalse(report["ready"])
            self.assertIsNone(report["available_ram_bytes"])
            self.assertNotIn("sensitive content", json.dumps(report))

    def test_disk_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("task004.preflight.shutil.disk_usage", side_effect=OSError("sensitive content")):
            report = check_preflight(Config(n_ctx=1), Path(directory))
            self.assertFalse(report["ready"])
            self.assertIsNone(report["free_disk_bytes"])
            self.assertNotIn("sensitive content", json.dumps(report))

    def test_linux_commit_is_explicitly_unavailable(self):
        with patch("task004.preflight.os.name", "posix"):
            result = windows_system_commit()
        self.assertIsNone(result["total_bytes"])
        self.assertIsNone(result["limit_bytes"])
        self.assertIsNone(result["available_bytes"])
        self.assertEqual(result["unavailable_reason"], "WINDOWS_ONLY")

    def test_report_identifies_host_and_measurement_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.measure(100, 200, directory)
        self.assertEqual(result["measurement_scope"], "CURRENT_HOST")
        self.assertEqual(result["available_ram_bytes"], 100)
        self.assertEqual(result["free_disk_bytes"], 200)
        self.assertTrue(result["observed_at_utc"].endswith("+00:00"))


if __name__ == "__main__":
    unittest.main()
