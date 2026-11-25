# scholarship-module

[![CI](https://github.com/hasgh34/scholarship-module/actions/workflows/ci.yml/badge.svg)](https://github.com/hasgh34/scholarship-module/actions/workflows/ci.yml)

Модуль расчёта стипендии и рейтинга студента по заданным критериям (учебная практика по МДК 02.02).

## Возможности

- **Расчёт стипендий:** академическая, повышенная (ПГАС), социальная; итог - сумма положенных выплат.
- **Рейтинг** 0-100: взвешенная сумма критериев (средний балл, НИР, общественная деятельность) и уровень.
- **Прозрачная конфигурация:** все суммы, пороги и веса лежат в [`config/rules.yaml`](config/rules.yaml), код менять не нужно.
- **Аудит:** для каждого критерия видно, кто и сколько баллов начислил; для каждой выплаты - почему она назначена или нет; все действия пишутся в `audit.jsonl`.
- **Экспорт в PDF** для приказа.
- **Unit-тесты** на граничные случаи: 0 баллов, максимум, пороги, льготы, задолженности, ошибки ввода.

## Правила (по умолчанию)

| Условие | Результат |
| --- | --- |
| Есть задолженности | Стипендии не начисляются, уровень рейтинга «Низкий» |
| Средний балл >= 4,0 | Академическая стипендия |
| Средний балл >= 4,5 и НИР >= 20 баллов | Повышенная (ПГАС) |
| Есть справка и нет задолженностей | Социальная стипендия |

Рейтинг = 50% * (средний балл / 5) + 30% * (НИР / 100) + 20% * (активность / 100), баллы сверх максимума обрезаются.

## Структура

```
src/scholarship/   calculator.py, config.py, audit.py, pdf_export.py, service.py, cli.py, models.py
config/rules.yaml  правила расчёта
tests/             unit-тесты (+ fixtures/rules_test.yaml)
docs/diagrams/     ER, Use Case, Sequence
examples/          пример входных данных
```

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m scholarship.cli --input examples/students.json --pdf order.pdf
```

Пример вывода:

```
Иванов И.И.: рейтинг 63.50 (Средний), выплата 7500
Петров П.П.: рейтинг 41.00 (Низкий), выплата 6000
Сидоров С.С.: рейтинг 55.00 (Низкий), выплата 0
PDF сохранён: order.pdf
```

Пример в коде:

```python
from decimal import Decimal
from scholarship.config import load_rules
from scholarship.calculator import calculate
from scholarship.models import ScoreEntry, StudentRecord

rules = load_rules("config/rules.yaml")
record = StudentRecord("Иванов И.И.", Decimal("4.8"), 0, False, "dekanat",
                       (ScoreEntry("research", 25, "nauch_ruk", "публикация"),))
result = calculate(record, rules)
print(result.rating, result.total, result.decisions)
```

## Тесты и качество кода

```bash
pytest --cov=src/scholarship --cov-report=term-missing
pre-commit install          # black + isort перед каждым коммитом
```

## Разработка

- Прямой push в `main` запрещён, изменения идут через Pull Request с Code Review и успешным CI.
- Ветки: `feature/ISSUE-ID-short-name`.
- Изменения версий: [CHANGELOG.md](CHANGELOG.md).
