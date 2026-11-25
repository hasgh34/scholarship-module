"""Журнал аудита: файл JSON Lines, записи только добавляются."""

import json
from datetime import datetime, timezone


class AuditLog:
    def __init__(self, path):
        self.path = path

    def write(self, actor, action, payload):
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "payload": payload,
        }
        with open(self.path, "a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def read(self):
        try:
            with open(self.path, encoding="utf-8") as file:
                return [json.loads(line) for line in file if line.strip()]
        except FileNotFoundError:
            return []


def result_to_dict(result):
    """Сериализует результат расчёта (включая расшифровку) для журнала."""
    return {
        "student_id": result.student_id,
        "rules_version": result.rules_version,
        "rating": str(result.rating),
        "level": result.level,
        "total": str(result.total),
        "payments": [{"code": p.code, "amount": str(p.amount)} for p in result.payments],
        "decisions": list(result.decisions),
        "audit": [
            {
                "criterion": a.criterion,
                "raw": str(a.raw_points),
                "capped": str(a.capped_points),
                "weight": str(a.weight),
                "contribution": str(a.contribution),
                "sources": [{"by": s[0], "points": str(s[1]), "comment": s[2]} for s in a.sources],
            }
            for a in result.audit
        ],
    }
