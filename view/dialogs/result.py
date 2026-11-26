"""
view/dialogs/result.py  —  ResultDialog: 인생 성적표 (FR-02-09, 상세 설계 14장 그림 7)

  - 상위 3명 시상대 (1위 왕관)
  - 표: 순위 · 이름 · 직업 · 돈 · 행복 × 10 · 총점 (점수 내림차순)
  - 버튼: 끝내기 / 한 판 더!  → play_again = True / False
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QSizePolicy

from common.adapter import pick, to_int
from common.constants import HAPPINESS_WEIGHT
from view import style
from view.painter_kit import draw_face, draw_crown, draw_sticker
from view.widgets import button, hbox, quiet
from view.dialogs.base import BaseDialog

PODIUM_COLORS = {1: "#FFD43B", 2: "#DCE2F0", 3: "#F4B07A"}


def read_ranking(ranking) -> list:
    """Model이 넘겨준 순위 목록을 [{name, job, money, happiness, score, character, is_npc, order}]로"""
    rows = []
    for i, r in enumerate(ranking):
        money = to_int(pick(r, ("money", "player_money"), 0))
        happiness = to_int(pick(r, ("happiness", "player_happiness"), 0))
        rows.append({
            "name": str(pick(r, ("name", "player_name"), "?")),
            "job": str(pick(r, ("job", "player_job"), "") or "-"),
            "money": money,
            "happiness": happiness,
            "score": to_int(pick(r, ("score",), money + happiness * HAPPINESS_WEIGHT)),
            "character": str(pick(r, ("character", "player_character"), "") or ""),
            "is_npc": bool(pick(r, ("is_npc",), False)),
            "order": to_int(pick(r, ("order",), i)),
        })
    rows.sort(key=lambda x: (x["score"], x["money"]), reverse=True)
    return rows


class Podium(QWidget):
    """시상대 그림: 가운데 1위, 왼쪽 2위, 오른쪽 3위"""

    def __init__(self, rows, parent=None):
        super().__init__(parent)
        self.rows = rows[:3]
        self.setFixedHeight(300)       # 1위 왕관까지 들어가는 높이
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        block = min(190, w / 3.4)
        heights = {1: 140, 2: 110, 3: 90}
        centers = {1: w / 2, 2: w / 2 - block * 1.08, 3: w / 2 + block * 1.08}
        base = self.height() - 6
        for rank, row in enumerate(self.rows, start=1):
            cx, h = centers[rank], heights[rank]
            rect = QRectF(cx - block / 2, base - h, block, h - 5)
            draw_sticker(p, rect, PODIUM_COLORS[rank], radius=14, outline=3.5, shadow=5,
                         lip=style.darker(PODIUM_COLORS[rank], 112))
            p.setPen(QColor(style.INK))
            p.setFont(style.title_font(46))
            p.drawText(QRectF(rect.left(), rect.top() + 4, rect.width(), 56), Qt.AlignCenter, str(rank))
            p.setFont(style.title_font(17))
            p.drawText(QRectF(rect.left(), rect.top() + 60, rect.width(), 26), Qt.AlignCenter, f"{row['score']:,}점")
            color = style.player_color_hex(row["order"])
            face = 62 if rank == 1 else 54
            face_rect = QRectF(cx - face / 2, rect.top() - face - 34, face, face)
            draw_face(p, face_rect, row["character"], color, row["is_npc"])
            p.setPen(QColor(style.INK))
            p.setFont(style.title_font(17))
            p.drawText(QRectF(cx - 110, rect.top() - 30, 220, 24), Qt.AlignCenter, f"{row['name']}  {row['job']}")
            if rank == 1:
                draw_crown(p, QRectF(cx - 20, face_rect.top() - 34, 40, 28), style.SUN)
        p.end()


class ResultDialog(BaseDialog):
    """게임 종료: 점수 내림차순 순위 표 + 시상대 (FR-02-09)"""

    def __init__(self, ranking, parent=None):
        super().__init__(parent, 820, "인생 성적표")
        rows = read_ranking(ranking)
        self.play_again = False

        logo = QLabel("".join(f"<span style='color:{c}'>{ch}</span>"
                              for ch, c in zip("인생 성적표", [style.CHERRY, style.GOLD, "#000", style.LEAF, style.POOL,
                                                           style.STORM])))
        logo.setFont(style.title_font(42))
        logo.setAlignment(Qt.AlignCenter)
        self.body.addWidget(logo)
        self.after_show = "confetti"
        note = quiet("모두 노년기까지 마쳤어요! 총점 = 돈(만원) + 행복 × 10", 13)
        note.setAlignment(Qt.AlignCenter)
        self.body.addWidget(note)
        self.body.addWidget(Podium(rows))

        table = QGridLayout()
        table.setHorizontalSpacing(18)
        table.setVerticalSpacing(4)
        heads = ["순위", "이름", "직업", "돈", "행복 × 10", "총점"]
        for col, text in enumerate(heads):
            head = QLabel(text)
            head.setStyleSheet(f"color: {style.TEXT_QUIET}; font-size: 12px;")
            table.addWidget(head, 0, col)
        for i, r in enumerate(rows, start=1):
            cells = [f"{i}위", r["name"], r["job"], style.format_money(r["money"]),
                     f"{r['happiness'] * HAPPINESS_WEIGHT:,}", f"{r['score']:,}"]
            for col, text in enumerate(cells):
                label = QLabel(text)
                label.setFont(style.title_font(15))
                if col == 1:
                    label.setStyleSheet(f"color: {style.player_color_hex(r['order'])};")
                table.addWidget(label, i, col)
        self.body.addLayout(table)

        finish = button("끝내기")
        finish.clicked.connect(self.reject)
        again = button("한 판 더!", role="primary", min_height=46)
        again.clicked.connect(self._again)
        self.body.addLayout(hbox("stretch", finish, again, spacing=10))

    def _again(self) -> None:
        self.play_again = True
        self.accept()
