"""Тесты конфигурации правил."""

import copy
import os
import tempfile
import unittest
from decimal import Decimal

import yaml

from scholarship.calculator import calculate
from scholarship.config import load_rules, parse_rules
from scholarship.errors import ConfigError

from .helpers import FIXTURE_RULES, student


def raw_rules():
    with open(FIXTURE_RULES, encoding="utf-8") as file:
        return yaml.safe_load(file)


class ConfigTests(unittest.TestCase):
    def test_loads_valid_file(self):
        rules = load_rules(FIXTURE_RULES)
        self.assertEqual(rules.version, "2026.1")
        self.assertEqual(rules.stipends["increased"].min_avg, Decimal("4.5"))

    def test_weights_must_sum_to_one(self):
        data = raw_rules()
        data["rating"]["weights"]["avg"] = 0.6
        with self.assertRaises(ConfigError):
            parse_rules(data)

    def test_missing_parameter(self):
        data = raw_rules()
        del data["stipends"]["social"]
        with self.assertRaises(ConfigError):
            parse_rules(data)

    def test_not_a_number(self):
        data = raw_rules()
        data["stipends"]["academic"]["amount"] = "много"
        with self.assertRaises(ConfigError):
            parse_rules(data)

    def test_negative_amount(self):
        data = raw_rules()
        data["stipends"]["academic"]["amount"] = -1
        with self.assertRaises(ConfigError):
            parse_rules(data)

    def test_zero_max_points(self):
        data = raw_rules()
        data["rating"]["max_points"]["research"] = 0
        with self.assertRaises(ConfigError):
            parse_rules(data)

    def test_empty_levels(self):
        data = raw_rules()
        data["rating"]["levels"] = []
        with self.assertRaises(ConfigError):
            parse_rules(data)

    def test_missing_file(self):
        with self.assertRaises(ConfigError):
            load_rules("no/such/file.yaml")

    def test_changing_config_changes_result_without_code_changes(self):
        data = raw_rules()
        data["stipends"]["academic"]["min_avg"] = 4.5
        stricter = parse_rules(copy.deepcopy(data))
        res = calculate(student(avg="4.2"), stricter)
        self.assertEqual(res.total, 0)

    def test_invalid_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.yaml")
            with open(path, "w", encoding="utf-8") as file:
                file.write("a: [unclosed")
            with self.assertRaises(ConfigError):
                load_rules(path)


if __name__ == "__main__":
    unittest.main()
