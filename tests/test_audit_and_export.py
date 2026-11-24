"""Тесты журнала аудита, пакетного расчёта, PDF и командной строки."""

import json
import os
import tempfile
import unittest

from scholarship.audit import AuditLog
from scholarship.cli import main
from scholarship.pdf_export import export_order_pdf
from scholarship.service import calculate_all

from .helpers import FIXTURE_RULES, rules, student

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "students.json")


class AuditLogTests(unittest.TestCase):
    def test_batch_is_logged_with_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = AuditLog(os.path.join(tmp, "audit.jsonl"))
            calculate_all([student(avg="4.6", research=30)], rules(), log, actor="komissiya")
            events = log.read()
        self.assertEqual([e["action"] for e in events],
                         ["batch_started", "student_calculated", "batch_finished"])
        calculated = events[1]
        self.assertEqual(calculated["actor"], "komissiya")
        research = next(a for a in calculated["payload"]["audit"] if a["criterion"] == "research")
        self.assertEqual(research["sources"][0]["by"], "nauch_ruk")

    def test_log_is_append_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = AuditLog(os.path.join(tmp, "audit.jsonl"))
            log.write("a", "first", {})
            log.write("b", "second", {})
            self.assertEqual([e["action"] for e in log.read()], ["first", "second"])

    def test_read_missing_file_returns_empty(self):
        self.assertEqual(AuditLog("no/such/audit.jsonl").read(), [])


class PdfExportTests(unittest.TestCase):
    def test_pdf_is_created(self):
        results = [
            *calculate_all([student(avg="4.6", research=30, student_id="Иванов")],
                           rules(), AuditLog(os.devnull), "t"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = export_order_pdf(results, os.path.join(tmp, "order.pdf"), "Приказ")
            with open(path, "rb") as file:
                data = file.read()
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 1000)

    def test_pdf_for_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = export_order_pdf([], os.path.join(tmp, "empty.pdf"), "Приказ")
            self.assertTrue(os.path.getsize(path) > 0)


class CliTests(unittest.TestCase):
    def test_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = os.path.join(tmp, "o.pdf")
            audit = os.path.join(tmp, "a.jsonl")
            code = main(["--input", EXAMPLE, "--rules", FIXTURE_RULES, "--audit", audit, "--pdf", pdf])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(pdf))
            with open(audit, encoding="utf-8") as file:
                self.assertEqual(len(file.readlines()), 5)  # старт + 3 студента + финиш

    def test_cli_reports_error(self):
        self.assertEqual(main(["--input", "no_such.json", "--rules", FIXTURE_RULES]), 1)

    def test_cli_bad_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(main(["--input", EXAMPLE, "--rules", os.path.join(tmp, "x.yaml")]), 1)

    def test_example_file_is_valid_json(self):
        with open(EXAMPLE, encoding="utf-8") as file:
            self.assertEqual(len(json.load(file)["students"]), 3)


if __name__ == "__main__":
    unittest.main()
