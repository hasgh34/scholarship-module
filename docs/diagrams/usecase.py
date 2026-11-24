"""Рисует UML Use Case диаграмму модуля (matplotlib)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, Circle

FS = 11
fig, ax = plt.subplots(figsize=(9.8, 8.8))
ax.set_xlim(0, 9.8); ax.set_ylim(0, 8.8); ax.set_aspect("equal"); ax.axis("off")

# граница системы
ax.add_patch(Rectangle((1.5, 0.45), 6.9, 8.0, fill=False, lw=1.6, ec="#222222"))
ax.text(4.95, 8.15, "Модуль расчёта стипендии и рейтинга студента", ha="center", va="center",
        fontsize=FS + 0.5, fontweight="bold")

def actor(x, y, label):
    ax.add_patch(Circle((x, y + 0.42), 0.13, fill=False, lw=1.4, ec="#222222"))
    ax.plot([x, x], [y + 0.29, y - 0.1], c="#222222", lw=1.4)
    ax.plot([x - 0.25, x + 0.25], [y + 0.18, y + 0.18], c="#222222", lw=1.4)
    ax.plot([x, x - 0.2], [y - 0.1, y - 0.42], c="#222222", lw=1.4)
    ax.plot([x, x + 0.2], [y - 0.1, y - 0.42], c="#222222", lw=1.4)
    ax.text(x, y - 0.55, label, ha="center", va="top", fontsize=FS - 1)
    return x, y

def usecase(x, y, w, h, text, color="#eaf1fb"):
    ax.add_patch(Ellipse((x, y), w, h, fc=color, ec="#222222", lw=1.3))
    ax.text(x, y, text, ha="center", va="center", fontsize=FS - 0.5)
    return x, y, w, h

def left_edge(uc):  return (uc[0] - uc[2] / 2, uc[1])
def right_edge(uc): return (uc[0] + uc[2] / 2, uc[1])

def link(p, q):
    ax.plot([p[0], q[0]], [p[1], q[1]], c="#222222", lw=1.2)

LX, LW, LH = 3.4, 3.3, 0.95
uc2 = usecase(LX, 7.3, LW, LH, "Начислить баллы НИР\nи общественной деятельности")
uc3 = usecase(LX, 6.1, LW, LH, "Настроить правила\nрасчёта (rules.yaml)")
uc1 = usecase(LX, 4.9, LW, LH, "Внести данные студента")
uc4 = usecase(LX, 3.7, LW, LH, "Рассчитать стипендию\nи рейтинг", "#fff2cc")
uc5 = usecase(LX, 2.5, LW, LH, "Экспортировать приказ\nв PDF")
uc6 = usecase(LX, 1.3, LW, LH, "Просмотреть журнал\nаудита")

RX, RW = 6.95, 2.5
uc7 = usecase(RX, 6.1, RW, LH, "Посмотреть свой\nрейтинг и стипендию")
inc1 = usecase(RX, 4.75, RW, LH, "Загрузить и проверить\nправила", "#f2f2f2")
inc2 = usecase(RX, 2.65, RW, LH, "Записать в журнал\nаудита", "#f2f2f2")

# актёры
resp = actor(0.75, 7.5, "Ответственный\n(научрук, куратор)")
adm = actor(0.75, 5.5, "Администратор")
dean = actor(0.75, 3.3, "Сотрудник\nдеканата")
stud = actor(9.2, 6.1, "Студент")

link((resp[0] + 0.25, resp[1] + 0.18), left_edge(uc2))
link((adm[0] + 0.25, adm[1] + 0.18), left_edge(uc3))
for uc in (uc1, uc4, uc5, uc6):
    link((dean[0] + 0.25, dean[1] + 0.18), left_edge(uc))
link((stud[0] - 0.25, stud[1] + 0.18), right_edge(uc7))

import math

def edge_point(uc, target):
    """Точка на границе эллипса uc в направлении центра target."""
    dx, dy = target[0] - uc[0], target[1] - uc[1]
    a, b = uc[2] / 2, uc[3] / 2
    t = 1 / math.sqrt((dx / a) ** 2 + (dy / b) ** 2)
    return uc[0] + dx * t, uc[1] + dy * t

def include(a, b):
    p, q = edge_point(a, b), edge_point(b, a)
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="->", ls="--", lw=1.2, color="#222222"))
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    dy = 0.2 if b[1] > a[1] else -0.2
    ax.text(mx - 0.05, my + dy, "«include»", ha="center", va="center", fontsize=FS - 2, style="italic",
            bbox=dict(fc="white", ec="none", pad=0.6))

include(uc4, inc1)
include(uc4, inc2)
plt.savefig("usecase.png", dpi=220, bbox_inches="tight", facecolor="white")
