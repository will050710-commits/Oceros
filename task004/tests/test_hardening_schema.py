"""A3/A4 regressions for bounded config and explicit schema contracts."""
import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from task004.cli import main
from task004.config import Config, ConfigError, parse_config
from task004.record import STATUS_REASONS
from task004.schema import validate, validate_artifact


ROOT = Path(__file__).resolve().parents[1]
BASELINE_EVIDENCE = ROOT / "evidence" / "dry-run" / "e1979d42784948cfbeb13b44cbc6044a"


def schema(name):
    return json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text())


class ConfigBoundsTests(unittest.TestCase):
    def test_a3_timeout_and_sampling_upper_bounds(self):
        for key, upper in (("timeout_s", 3600), ("startup_timeout_s", 3600),
                           ("mock_delay_s", 3600), ("sample_interval_s", 60)):
            with self.subTest(key=key, value=upper):
                self.assertEqual(getattr(parse_config({"n_ctx": 1, key: upper}), key), upper)
            for value in (upper + .001, 1e10, 1e300):
                with self.subTest(key=key, value=value), self.assertRaises(ConfigError):
                    parse_config({"n_ctx": 1, key: value})

    def test_a3_validate_config_rejects_extreme_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            for key in ("timeout_s", "startup_timeout_s", "mock_delay_s", "sample_interval_s"):
                for value in (1e10, 1e300):
                    config_path.write_text(json.dumps({"n_ctx": 1, key: value}))
                    capture = io.StringIO()
                    with self.subTest(key=key, value=value), contextlib.redirect_stdout(capture):
                        result = main(["validate-config", "--config", str(config_path)])
                        self.assertEqual(result, 2)
                        self.assertEqual(json.loads(capture.getvalue())["status"], "CONFIG_ERROR")


class SchemaContractTests(unittest.TestCase):
    def test_a4_config_and_manifest_numerical_boundaries_match(self):
        config_schema = schema("manifest")["properties"]["config"]
        # Expected outcomes are explicit, so simultaneous weakening is detected.
        boundaries = {
            "n_ctx": [(0, False), (1, True), (2, True)],
            "max_new_tokens": [(0, False), (1, True), (2, True), (95, True), (96, True), (97, False)],
            "timeout_s": [(-.001, False), (0, False), (.001, True), (3599.999, True), (3600, True), (3600.001, False)],
            "startup_timeout_s": [(-.001, False), (0, False), (.001, True), (3599.999, True), (3600, True), (3600.001, False)],
            "sample_interval_s": [(.009, False), (.01, True), (.011, True), (59.999, True), (60, True), (60.001, False)],
            "mock_delay_s": [(-.001, False), (0, True), (.001, True), (3599.999, True), (3600, True), (3600.001, False)],
            "min_available_ram_bytes": [(-1, False), (0, True), (1, True)],
            "min_free_disk_bytes": [(-1, False), (0, True), (1, True)],
            "image_long_edge_px": [(0, False), (1, True), (2, True), (767, True), (768, True), (769, False)],
            "max_image_tokens": [(0, False), (1, True), (2, True)],
        }
        for key, cases in boundaries.items():
            for value, expected in cases:
                with self.subTest(key=key, value=value):
                    data = Config(n_ctx=1).to_dict()
                    if key in ("image_long_edge_px", "max_image_tokens"):
                        data.update(image_long_edge_px=64, max_image_tokens=16)
                    data[key] = value
                    try:
                        parse_config(data)
                        config_accepts = True
                    except ConfigError:
                        config_accepts = False
                    try:
                        validate(data, config_schema)
                        schema_accepts = True
                    except ValueError:
                        schema_accepts = False
                    self.assertEqual(config_accepts, expected)
                    self.assertEqual(schema_accepts, expected)

    def test_a4_every_pattern_is_anchored(self):
        def inspect(node):
            if "pattern" in node:
                self.assertTrue(node["pattern"].startswith("^"), node["pattern"])
                self.assertTrue(node["pattern"].endswith("$"), node["pattern"])
            for child in node.get("properties", {}).values():
                inspect(child)
            if "items" in node:
                inspect(node["items"])
        inspect(schema("run"))
        inspect(schema("manifest"))

    def test_a4_reason_enum_matches_status_reasons(self):
        actual = schema("run")["properties"]["reason_code"].get("enum", [])
        self.assertEqual(set(actual), set().union(*STATUS_REASONS.values()))
        self.assertEqual(len(actual), len(set(actual)))

    def test_a4_unsupported_keywords_fail_at_every_depth(self):
        from task004.schema import check_schema
        for invalid in (
            {"format": "date-time"},
            {"properties": {"child": {"format": "date-time"}}},
            {"items": {"properties": {"child": {"not": {}}}}},
            {"properties": {"array": {"items": {"allOf": []}}}},
        ):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "SCHEMA_UNSUPPORTED_KEYWORD"):
                check_schema(invalid)
        for name in ("run", "manifest"):
            check_schema(schema(name))

    def test_a4_validate_artifact_checks_schema_before_value(self):
        invalid = {"type": "object", "properties": {"ignored": {"format": "anything"}}}
        with patch("task004.schema.Path.read_text", return_value=json.dumps(invalid)):
            with self.assertRaisesRegex(ValueError, "SCHEMA_UNSUPPORTED_KEYWORD"):
                validate_artifact({}, "manifest")

    def test_a4_maximum_and_exclusive_minimum_enforced(self):
        contract = {"type": "number", "exclusiveMinimum": 0, "maximum": 1}
        validate(.001, contract)
        validate(1, contract)
        for value in (-.001, 0, 1.001):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate(value, contract)

    def test_a4_run_schema_rejects_bad_reason_time_token_and_id(self):
        baseline = json.loads((BASELINE_EVIDENCE / "runs.jsonl").read_text())
        invalid_cases = [
            ("reason_code", "UNREGISTERED"),
            ("started_at_utc", "not-a-timestamp"),
            ("finished_at_utc", "2026-11-06T00:00:00+07:00"),
            ("run_id", "ZZ" + baseline["run_id"] + "ZZ"),
        ]
        for key, value in invalid_cases:
            broken = deepcopy(baseline)
            broken[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_artifact(broken, "run")
        broken = deepcopy(baseline)
        broken["metrics"]["synthetic_output_tokens"] = 1.5
        with self.assertRaises(ValueError):
            validate_artifact(broken, "run")

    def test_a4_existing_committed_evidence_remains_valid(self):
        manifest = json.loads((BASELINE_EVIDENCE / "manifest.json").read_text())
        run = json.loads((BASELINE_EVIDENCE / "runs.jsonl").read_text())
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(run["schema_version"], 1)
        validate_artifact(manifest, "manifest")
        validate_artifact(run, "run")

    def test_a4_malformed_supported_keyword_forms_fail_closed(self):
        from task004.schema import check_schema
        for malformed in ({"type": "bogus"}, {"type": []}, {"properties": []},
                          {"required": "name"}, {"items": []}, {"maximum": True},
                          {"additionalProperties": {"type": "string"}}, {"enum": []}):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                check_schema(malformed)


if __name__ == "__main__":
    unittest.main()
