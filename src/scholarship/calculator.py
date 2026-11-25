"""Расчёт стипендии и рейтинга студента."""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from .errors import InvalidInputError
from .models import (
    ACTIVITY,
    RESEARCH,
    SCORE_CRITERIA,
    AuditLine,
    Payment,
    Result,
)

CENT = Decimal("0.01")
ZERO = Decimal("0")
MAX_AVG = Decimal("5")


def _round(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _validate(record):
    if not record.student_id:
        raise InvalidInputError("Не указан идентификатор студента")
    if not ZERO <= record.avg_score <= MAX_AVG:
        raise InvalidInputError(f"Средний балл вне диапазона 0-5: {record.avg_score}")
    if record.debts < 0:
        raise InvalidInputError(f"Число задолженностей не может быть отрицательным: {record.debts}")
    for entry in record.entries:
        if entry.criterion not in SCORE_CRITERIA:
            raise InvalidInputError(f"Неизвестный критерий: {entry.criterion}")
        if entry.points < 0:
            raise InvalidInputError(f"Отрицательные баллы ({entry.criterion}): {entry.points}")


def _rating(record, rules):
    """Считает рейтинг и расшифровку по критериям."""
    grouped = defaultdict(list)
    for entry in record.entries:
        grouped[entry.criterion].append(entry)
    research = sum((Decimal(e.points) for e in grouped[RESEARCH]), ZERO)
    activity = sum((Decimal(e.points) for e in grouped[ACTIVITY]), ZERO)

    raw = {"avg": record.avg_score, "research": research, "activity": activity}
    sources = {
        "avg": ((record.entered_by, record.avg_score, "средний балл за сессию"),),
        "research": tuple((e.awarded_by, Decimal(e.points), e.comment) for e in grouped[RESEARCH]),
        "activity": tuple((e.awarded_by, Decimal(e.points), e.comment) for e in grouped[ACTIVITY]),
    }
    lines, rating = [], ZERO
    for code in ("avg", "research", "activity"):
        limit = rules.max_points[code]
        capped = min(raw[code], limit)
        contribution = capped / limit * rules.weights[code] * 100
        rating += contribution
        lines.append(
            AuditLine(code, raw[code], capped, limit, rules.weights[code],
                      _round(contribution), sources[code])
        )
    return _round(rating), tuple(lines), research


def _payments(record, rules, research):
    """Определяет положенные выплаты и записывает причины решений."""
    payments, decisions = [], []
    st = rules.stipends

    if record.debts > 0:
        decisions.append(f"Стипендии не начисляются: есть задолженности ({record.debts})")
        return payments, decisions

    acad = st["academic"]
    if record.avg_score >= acad.min_avg:
        payments.append(Payment(acad.code, acad.title, acad.amount))
        decisions.append(f"{acad.title}: средний балл {record.avg_score} >= {acad.min_avg}")
    else:
        decisions.append(f"{acad.title} не назначена: средний балл {record.avg_score} < {acad.min_avg}")

    inc = st["increased"]
    if record.avg_score >= inc.min_avg and research >= inc.min_research_points:
        payments.append(Payment(inc.code, inc.title, inc.amount))
        decisions.append(
            f"{inc.title}: средний балл {record.avg_score} >= {inc.min_avg}, "
            f"НИР {research} >= {inc.min_research_points}"
        )
    else:
        decisions.append(
            f"{inc.title} не назначена: нужен средний балл >= {inc.min_avg} "
            f"и НИР >= {inc.min_research_points} "
            f"(есть {record.avg_score} и {research})"
        )

    soc = st["social"]
    if record.has_social_certificate:
        payments.append(Payment(soc.code, soc.title, soc.amount))
        decisions.append(f"{soc.title}: справка есть, задолженностей нет")
    else:
        decisions.append(f"{soc.title} не назначена: нет подтверждающей справки")
    return payments, decisions


def calculate(record, rules):
    """Главная функция: StudentRecord + RuleSet -> Result."""
    _validate(record)
    rating, audit, research = _rating(record, rules)
    payments, decisions = _payments(record, rules, research)

    if record.debts > 0:
        level = rules.debt_level
    else:
        level = next((lv.name for lv in rules.levels if rating >= lv.min_rating), rules.debt_level)

    total = sum((p.amount for p in payments), ZERO)
    return Result(
        student_id=record.student_id,
        rules_version=rules.version,
        rating=rating,
        level=level,
        payments=tuple(payments),
        total=total,
        audit=audit,
        decisions=tuple(decisions),
    )
