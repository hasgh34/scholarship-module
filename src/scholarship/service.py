"""Пакетный расчёт с записью в журнал аудита."""

from .audit import result_to_dict
from .calculator import calculate


def calculate_all(records, rules, audit_log, actor):
    """Считает всех студентов и фиксирует в журнале входные данные и результат."""
    audit_log.write(actor, "batch_started",
                    {"students": len(records), "rules_version": rules.version})
    results = []
    for record in records:
        result = calculate(record, rules)
        audit_log.write(actor, "student_calculated", result_to_dict(result))
        results.append(result)
    audit_log.write(actor, "batch_finished", {"students": len(results)})
    return results
