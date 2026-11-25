"""Командная строка: python -m scholarship.cli --input data.json --pdf order.pdf"""

import argparse
import json
import sys
from decimal import Decimal

from .audit import AuditLog
from .config import load_rules
from .errors import ScholarshipError
from .models import ScoreEntry, StudentRecord
from .pdf_export import export_order_pdf
from .service import calculate_all


def load_records(path):
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    records = []
    for item in data["students"]:
        entries = tuple(ScoreEntry(e["criterion"], int(e["points"]), e["awarded_by"], e.get("comment", ""))
                        for e in item.get("entries", []))
        records.append(StudentRecord(
            student_id=item["student_id"],
            avg_score=Decimal(str(item["avg_score"])),
            debts=int(item["debts"]),
            has_social_certificate=bool(item["has_social_certificate"]),
            entered_by=item["entered_by"],
            entries=entries,
        ))
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description="Расчёт стипендии и рейтинга студентов")
    parser.add_argument("--input", required=True, help="JSON со студентами")
    parser.add_argument("--rules", default="config/rules.yaml", help="файл правил")
    parser.add_argument("--audit", default="audit.jsonl", help="журнал аудита")
    parser.add_argument("--pdf", help="куда сохранить PDF для приказа")
    parser.add_argument("--actor", default="cli", help="кто запускает расчёт")
    args = parser.parse_args(argv)
    try:
        rules = load_rules(args.rules)
        results = calculate_all(load_records(args.input), rules, AuditLog(args.audit), args.actor)
    except (ScholarshipError, OSError, KeyError, ValueError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    for res in results:
        print(f"{res.student_id}: рейтинг {res.rating} ({res.level}), выплата {res.total}")
    if args.pdf:
        export_order_pdf(results, args.pdf, "Выписка из приказа о назначении стипендий")
        print(f"PDF сохранён: {args.pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
