"""Общие вспомогательные функции для тестов."""

import os
from decimal import Decimal

from scholarship.config import load_rules
from scholarship.models import ScoreEntry, StudentRecord

FIXTURE_RULES = os.path.join(os.path.dirname(__file__), "fixtures", "rules_test.yaml")


def rules():
    return load_rules(FIXTURE_RULES)


def student(avg="4.0", debts=0, certificate=False, research=0, activity=0, student_id="S1"):
    """Собирает StudentRecord; баллы НИР и активности вносят разные люди."""
    entries = []
    if research:
        entries.append(ScoreEntry("research", research, "nauch_ruk", "НИР"))
    if activity:
        entries.append(ScoreEntry("activity", activity, "kurator", "активность"))
    return StudentRecord(student_id, Decimal(str(avg)), debts, certificate, "dekanat", tuple(entries))
