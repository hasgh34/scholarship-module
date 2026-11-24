"""Модели данных."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Tuple

RESEARCH = "research"
ACTIVITY = "activity"
SCORE_CRITERIA = (RESEARCH, ACTIVITY)


@dataclass(frozen=True)
class ScoreEntry:
    """Начисление баллов: кто, по какому критерию и сколько."""

    criterion: str  # research | activity
    points: int
    awarded_by: str
    comment: str = ""


@dataclass(frozen=True)
class StudentRecord:
    """Исходные данные студента за период."""

    student_id: str
    avg_score: Decimal
    debts: int
    has_social_certificate: bool
    entered_by: str
    entries: Tuple[ScoreEntry, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class StipendRule:
    code: str
    title: str
    amount: Decimal
    min_avg: Optional[Decimal] = None
    min_research_points: Optional[Decimal] = None


@dataclass(frozen=True)
class Level:
    name: str
    min_rating: Decimal


@dataclass(frozen=True)
class RuleSet:
    """Набор правил, загруженный из конфигурации."""

    version: str
    stipends: dict
    weights: dict
    max_points: dict
    levels: Tuple[Level, ...]
    debt_level: str


@dataclass(frozen=True)
class Payment:
    code: str
    title: str
    amount: Decimal


@dataclass(frozen=True)
class AuditLine:
    """Строка расшифровки рейтинга по одному критерию."""

    criterion: str
    raw_points: Decimal
    capped_points: Decimal
    max_points: Decimal
    weight: Decimal
    contribution: Decimal
    sources: Tuple[Tuple[str, Decimal, str], ...]  # (кто, баллы, комментарий)


@dataclass(frozen=True)
class Result:
    student_id: str
    rules_version: str
    rating: Decimal
    level: str
    payments: Tuple[Payment, ...]
    total: Decimal
    audit: Tuple[AuditLine, ...]
    decisions: Tuple[str, ...]  # почему выплата назначена или нет
