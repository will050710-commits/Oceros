import ast
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from task004.record import STATUS_REASONS, source_provenance, validate_record
from task004.tests.fixtures import artifact_fixture


class ReviewRecordTests(unittest.TestCase):
    def test_malformed_provenance_is_always_safe_valueerror(self):
        valid = {'file': 'card.md', 'bytes': 1, 'sha256': '0'*64}
        cases = [None, [], {}, {'sources': None}, {'sources': [None]}, {'sources': [{}]},
                 {'sources': [{**valid, 'file': ['bad']}]}, {'sources': [{**valid, 'sha256': None}]},
                 {'sources': [{**valid, 'bytes': True}]}, {'sources': [{**valid, 'file': '../bad'}]},
                 {'sources': [{**valid, 'file': r'..\bad'}]}, {'sources': [valid, valid]}]
        for index in cases:
            with self.subTest(index=index), patch('task004.record.Path.read_text', return_value=json.dumps(index)):
                with self.assertRaises(ValueError):
                    source_provenance()

    def test_all_literal_client_and_server_errors_are_registered(self):
        root = Path(__file__).resolve().parents[1]
        codes = set()
        for name in ('client.py', 'server.py'):
            for node in ast.walk(ast.parse((root/name).read_text())):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id in ('ClientError', 'ServerError') and node.args
                        and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                    codes.add(node.args[0].value)
        self.assertGreater(len(codes), 10)
        self.assertEqual(codes - set().union(*STATUS_REASONS.values()), set())

    def test_pass_requires_positive_resource_evidence(self):
        _, record, _ = artifact_fixture()
        validate_record(record)
        for resources in (None, {**record['resources'], 'samples': 0}, {**record['resources'], 'rss_peak_bytes': None},
                          {**record['resources'], 'rss_peak_bytes': 0}, {**record['resources'], 'samples': True}):
            with self.subTest(resources=resources):
                broken = deepcopy(record)
                broken['resources'] = resources
                with self.assertRaises(ValueError):
                    validate_record(broken)
