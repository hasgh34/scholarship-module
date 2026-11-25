"""Загрузка и проверка файла правил."""

from decimal import Decimal, InvalidOperation

import yaml

from .errors import ConfigError
from .models import Level, RuleSet, StipendRule

REQUIRED_STIPENDS = ("academic", "increased", "social")
CRITERIA = ("avg", "research", "activity")


def _dec(value, name):
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ConfigError(f"Параметр {name}: ожидается число, получено {value!r}") from exc
    if result < 0:
        raise ConfigError(f"Параметр {name} не может быть отрицательным")
    return result


def parse_rules(data):
    """Строит RuleSet из словаря (результат разбора YAML)."""
    try:
        stipends = {}
        for code in REQUIRED_STIPENDS:
            raw = data["stipends"][code]
            stipends[code] = StipendRule(
                code=code,
                title=raw["title"],
                amount=_dec(raw["amount"], f"stipends.{code}.amount"),
                min_avg=_dec(raw["min_avg"], f"{code}.min_avg") if "min_avg" in raw else None,
                min_research_points=(
                    _dec(raw["min_research_points"], f"{code}.min_research_points")
                    if "min_research_points" in raw
                    else None
                ),
            )
        weights = {c: _dec(data["rating"]["weights"][c], f"weights.{c}") for c in CRITERIA}
        max_points = {c: _dec(data["rating"]["max_points"][c], f"max_points.{c}") for c in CRITERIA}
        levels = tuple(
            sorted(
                (Level(x["name"], _dec(x["min_rating"], "levels.min_rating"))
                 for x in data["rating"]["levels"]),
                key=lambda lv: lv.min_rating,
                reverse=True,
            )
        )
        version = str(data["version"])
        debt_level = data["rating"]["debt_level"]
    except (KeyError, TypeError) as exc:
        raise ConfigError(f"В файле правил не хватает параметра: {exc}") from exc

    if sum(weights.values()) != Decimal("1"):
        raise ConfigError("Сумма весов критериев рейтинга должна быть равна 1")
    if any(m == 0 for m in max_points.values()):
        raise ConfigError("Максимум баллов по критерию должен быть больше нуля")
    if not levels:
        raise ConfigError("Не заданы уровни рейтинга")
    return RuleSet(version, stipends, weights, max_points, levels, debt_level)


def load_rules(path):
    """Читает YAML-файл правил."""
    try:
        with open(path, encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"Не удалось прочитать {path}: {exc}") from exc
    return parse_rules(data)
