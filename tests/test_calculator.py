"""Unit-тесты расчёта: нули, максимум, границы порогов, льготы, ошибки."""

import unittest
from decimal import Decimal

from scholarship.calculator import calculate
from scholarship.errors import InvalidInputError
from scholarship.models import ScoreEntry, StudentRecord

from .helpers import rules, student


def codes(result):
    return [p.code for p in result.payments]


class ZeroAndMaxTests(unittest.TestCase):
    def setUp(self):
        self.rules = rules()

    def test_zero_everything(self):
        res = calculate(student(avg="0"), self.rules)
        self.assertEqual(res.rating, Decimal("0.00"))
        self.assertEqual(res.level, "Низкий")
        self.assertEqual(res.total, 0)
        self.assertEqual(codes(res), [])

    def test_maximum_everything(self):
        res = calculate(student(avg="5", research=100, activity=100, certificate=True), self.rules)
        self.assertEqual(res.rating, Decimal("100.00"))
        self.assertEqual(res.level, "Высокий")
        self.assertEqual(codes(res), ["academic", "increased", "social"])
        self.assertEqual(res.total, Decimal("11000"))

    def test_points_above_maximum_are_capped(self):
        res = calculate(student(avg="5", research=250, activity=300), self.rules)
        self.assertEqual(res.rating, Decimal("100.00"))
        research_line = next(a for a in res.audit if a.criterion == "research")
        self.assertEqual(research_line.raw_points, 250)
        self.assertEqual(research_line.capped_points, 100)


class ThresholdTests(unittest.TestCase):
    def setUp(self):
        self.rules = rules()

    def test_academic_boundary(self):
        for avg, expected in (("4.0", True), ("3.99", False), ("4.01", True)):
            with self.subTest(avg=avg):
                res = calculate(student(avg=avg), self.rules)
                self.assertEqual("academic" in codes(res), expected)

    def test_increased_boundary_on_average(self):
        for avg, expected in (("4.5", True), ("4.49", False)):
            with self.subTest(avg=avg):
                res = calculate(student(avg=avg, research=20), self.rules)
                self.assertEqual("increased" in codes(res), expected)

    def test_increased_boundary_on_research(self):
        for points, expected in ((20, True), (19, False), (0, False)):
            with self.subTest(research=points):
                res = calculate(student(avg="4.5", research=points), self.rules)
                self.assertEqual("increased" in codes(res), expected)

    def test_research_points_are_summed_over_entries(self):
        record = StudentRecord("S1", Decimal("4.6"), 0, False, "dekanat", (
            ScoreEntry("research", 10, "nauch_ruk", "конференция"),
            ScoreEntry("research", 10, "nauch_ruk2", "публикация"),
        ))
        self.assertIn("increased", codes(calculate(record, self.rules)))

    def test_level_boundaries(self):
        cases = (
            # (avg, НИР, активность, ожидаемый рейтинг, ожидаемый уровень)
            ("5", 50, 50, "75.00", "Высокий"),   # ровно на границе 75
            ("5", 50, 49, "74.80", "Средний"),   # чуть ниже границы
            ("5", 0, 0, "50.00", "Средний"),     # ровно на границе 50
            ("4.99", 0, 0, "49.90", "Низкий"),   # чуть ниже границы
        )
        for avg, research, activity, rating, level in cases:
            with self.subTest(avg=avg, research=research, activity=activity):
                res = calculate(student(avg=avg, research=research, activity=activity), self.rules)
                self.assertEqual(res.rating, Decimal(rating))
                self.assertEqual(res.level, level)


class BenefitAndDebtTests(unittest.TestCase):
    def setUp(self):
        self.rules = rules()

    def test_social_only_with_certificate(self):
        res = calculate(student(avg="3.0", certificate=True), self.rules)
        self.assertEqual(codes(res), ["social"])
        self.assertEqual(res.total, Decimal("3500"))

    def test_social_requires_certificate(self):
        res = calculate(student(avg="3.0", certificate=False), self.rules)
        self.assertEqual(codes(res), [])

    def test_debt_cancels_all_stipends_even_social(self):
        res = calculate(student(avg="5", debts=1, certificate=True, research=100), self.rules)
        self.assertEqual(res.total, 0)
        self.assertEqual(codes(res), [])
        self.assertEqual(res.level, "Низкий")

    def test_debt_keeps_numeric_rating_visible(self):
        res = calculate(student(avg="5", debts=2, research=100, activity=100), self.rules)
        self.assertEqual(res.rating, Decimal("100.00"))
        self.assertEqual(res.level, "Низкий")

    def test_total_is_sum_of_payments(self):
        res = calculate(student(avg="4.6", research=30, certificate=True), self.rules)
        self.assertEqual(res.total, Decimal("11000"))


class AuditTests(unittest.TestCase):
    def test_audit_shows_who_gave_points_and_by_which_criterion(self):
        res = calculate(student(avg="4.2", research=30, activity=10), rules())
        by_criterion = {a.criterion: a for a in res.audit}
        self.assertEqual(by_criterion["research"].sources[0][0], "nauch_ruk")
        self.assertEqual(by_criterion["activity"].sources[0][0], "kurator")
        self.assertEqual(by_criterion["avg"].sources[0][0], "dekanat")

    def test_contributions_sum_to_rating(self):
        res = calculate(student(avg="4.3", research=33, activity=17), rules())
        self.assertEqual(sum(a.contribution for a in res.audit), res.rating)

    def test_decisions_explain_refusal(self):
        res = calculate(student(avg="4.5", research=19), rules())
        self.assertTrue(any("не назначена" in d and "НИР" in d for d in res.decisions))

    def test_result_remembers_rules_version(self):
        self.assertEqual(calculate(student(), rules()).rules_version, "2026.1")


class InvalidInputTests(unittest.TestCase):
    def setUp(self):
        self.rules = rules()

    def test_invalid_average(self):
        for avg in ("-0.1", "5.01"):
            with self.subTest(avg=avg):
                with self.assertRaises(InvalidInputError):
                    calculate(student(avg=avg), self.rules)

    def test_negative_debts(self):
        with self.assertRaises(InvalidInputError):
            calculate(student(debts=-1), self.rules)

    def test_negative_points(self):
        record = StudentRecord("S1", Decimal("4"), 0, False, "dekanat",
                               (ScoreEntry("research", -5, "x"),))
        with self.assertRaises(InvalidInputError):
            calculate(record, self.rules)

    def test_unknown_criterion(self):
        record = StudentRecord("S1", Decimal("4"), 0, False, "dekanat",
                               (ScoreEntry("magic", 5, "x"),))
        with self.assertRaises(InvalidInputError):
            calculate(record, self.rules)

    def test_empty_student_id(self):
        with self.assertRaises(InvalidInputError):
            calculate(student(student_id=""), self.rules)


if __name__ == "__main__":
    unittest.main()
