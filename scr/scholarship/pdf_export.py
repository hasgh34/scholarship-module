"""Экспорт результатов в PDF для приказа."""

import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FONT_NAME = "DejaVu"
DEFAULT_FONT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "DejaVuSans.ttf")


def _register_font(font_path):
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))


def export_order_pdf(results, path, title, font_path=DEFAULT_FONT, order_date=None):
    """Формирует PDF: таблица выплат по студентам, итог, версия правил, подписи."""
    _register_font(font_path)
    base = ParagraphStyle("base", fontName=FONT_NAME, fontSize=10, leading=13)
    head = ParagraphStyle("head", parent=base, fontSize=14, leading=18, spaceAfter=8)

    rows = [["№", "Студент", "Рейтинг", "Уровень", "Назначенные стипендии", "Итого, руб."]]
    for number, res in enumerate(results, start=1):
        names = ", ".join(p.title for p in res.payments) or "не назначена"
        rows.append([number, res.student_id, str(res.rating), res.level, Paragraph(names, base),
                     f"{res.total:.2f}"])
    grand_total = sum((r.total for r in results), 0)
    rows.append(["", "", "", "", "ВСЕГО", f"{grand_total:.2f}"])

    table = Table(rows, repeatRows=1, colWidths=[10 * mm, 38 * mm, 20 * mm, 22 * mm, 55 * mm, 25 * mm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (5, 0), (5, -1), "RIGHT"),
    ]))

    version = results[0].rules_version if results else "-"
    day = (order_date or date.today()).strftime("%d.%m.%Y")
    doc = SimpleDocTemplate(path, pagesize=A4, title=title,
                            leftMargin=20 * mm, rightMargin=15 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm)
    doc.build([
        Paragraph(title, head),
        Paragraph(f"Дата формирования: {day}. Версия правил расчёта: {version}.", base),
        Spacer(1, 8 * mm),
        table,
        Spacer(1, 15 * mm),
        Paragraph("Председатель стипендиальной комиссии ____________ / ______________", base),
        Spacer(1, 6 * mm),
        Paragraph("Секретарь комиссии ____________ / ______________", base),
    ])
    return path
