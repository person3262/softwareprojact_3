"""
view/dice_view.py  —  DiceView: 주사위 2개 결과 출력 (FR-02-05) + 조작 버튼

  DiceView (보드 가운데에 들어간다)
   ├─ DieFace × 2      주사위 그림 (QPainter로 직접 그림, 이미지 파일 불필요)
   ├─ move_badge       "7칸!" 별 배지
   ├─ roll_button      "주사위 굴리기!"   ← 클릭 감지는 Input이 한다 (View는 버튼만 제공)
   │                   투자 단계(한 턴의 순서 7번)에서는 "턴 마치기"로 바뀐다 (set_end_mode)
   └─ invest_button    "투자하기"         ← 투자 기회 턴에만 보인다 (FR-01-16)

굴리기 연출: 주사위가 이리저리 돌며 튀다가(0.6초) 결과 눈에서 멈추고, 별 배지가 툭 튀어나온다.
"""
from __future__ import annotations

import math
import random

from PyQt5.QtCore import Qt, QRectF, QTimer, QPointF, QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSizePolicy

from view import style
from view.widgets import button
from view.painter_kit import draw_sticker, draw_burst

ROLL_FRAMES = 11     # 굴러가는 연출 프레임 수
FRAME_MS = 55        # 프레임 간격(ms) → 약 0.6초

# 3×3 칸 중 점이 찍히는 위치 (열, 행)
PIPS = {
    1: [(1, 1)],
    2: [(0, 0), (2, 2)],
    3: [(0, 0), (1, 1), (2, 2)],
    4: [(0, 0), (2, 0), (0, 2), (2, 2)],
    5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],
    6: [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)],
}


class DieFace(QWidget):
    """주사위 한 개 그림. tilt(기울기)와 jump(튀어 오른 높이)를 바꿔 가며 굴린다."""

    def __init__(self, tilt: float = 0.0, parent=None):
        super().__init__(parent)
        self.value = 0        # 0 = 아직 안 굴림(빈 주사위)
        self.base_tilt = tilt
        self.tilt = tilt
        self.jump = 0.0
        self.setFixedSize(84, 92)

    def set_value(self, value: int) -> None:
        self.value = value
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        side = 60
        cx, cy = self.width() / 2, self.height() / 2 + 6
        # 바닥 그림자 (뛰어오를수록 작게)
        shrink = 1 - min(0.5, self.jump / 40)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(35, 38, 74, 70))
        p.drawEllipse(QPointF(cx, cy + side / 2 + 6), side * 0.5 * shrink, 6 * shrink)
        p.translate(cx, cy - self.jump)
        p.rotate(self.tilt)
        rect = QRectF(-side / 2, -side / 2, side, side)
        draw_sticker(p, rect, style.PAPER, radius=15, outline=3.5, shadow=5, lip="#E9ECF6")
        if self.value:
            cell = side / 4
            p.setPen(Qt.NoPen)
            for col, row in PIPS[self.value]:
                c = QPointF(rect.left() + cell * (col + 1), rect.top() + cell * (row + 1) - 1)
                p.setBrush(QBrush(QColor(style.CHERRY if self.value == 1 else style.INK)))
                p.drawEllipse(c, side * 0.085, side * 0.085)
        else:
            p.setPen(QColor(style.CARD_LINE))
            p.setFont(style.title_font(30))
            p.drawText(rect.adjusted(0, -3, 0, -3), Qt.AlignCenter, "?")
        p.end()


class MoveBadge(QWidget):
    """'7칸!' 별 배지. pop()으로 툭 튀어나온다."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.text = ""
        self.scale = 0.0
        self.setFixedSize(96, 96)
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(380)
        self.anim.setStartValue(0.2)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutBack)
        self.anim.valueChanged.connect(self._on_scale)

    def _on_scale(self, value) -> None:
        self.scale = float(value)
        self.update()

    def pop(self, text: str) -> None:
        self.text = text
        self.anim.stop()
        self.anim.start()

    def clear(self) -> None:
        self.anim.stop()
        self.text, self.scale = "", 0.0
        self.update()

    def paintEvent(self, event) -> None:
        if not self.text or self.scale <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2 - 2)
        p.scale(self.scale, self.scale)
        p.rotate(-8)
        draw_burst(p, QPointF(0, 0), 40, style.SUN, points=12, outline=3)
        p.setPen(QColor(style.INK))
        p.setFont(style.title_font(25))
        p.drawText(QRectF(-40, -20, 80, 38), Qt.AlignCenter, self.text)
        p.end()


class DiceView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.die1 = DieFace(-8)
        self.die2 = DieFace(9)
        self.move_badge = MoveBadge()

        self.roll_button = button("주사위 굴리기!", role="primary", min_height=50)
        self.roll_button.setFont(style.title_font(21))
        self.roll_button.setMinimumWidth(250)
        self.roll_button.setEnabled(False)
        self.invest_button = button("투자하기", min_height=50)
        self.invest_button.setFont(style.title_font(18))
        self.invest_button.setEnabled(False)
        self.invest_button.setVisible(False)

        dice_row = QHBoxLayout()
        dice_row.setSpacing(6)
        dice_row.addStretch(1)
        dice_row.addWidget(self.die1)
        dice_row.addWidget(self.die2)
        dice_row.addWidget(self.move_badge)
        dice_row.addStretch(1)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        buttons.addWidget(self.roll_button)
        buttons.addWidget(self.invest_button)
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addLayout(dice_row)
        layout.addLayout(buttons)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._frame)
        self._frames_left = 0
        self._result = (0, 0)
        self._on_done = None

    # ── Window가 부르는 함수 ─────────────────────────────────────
    def show_result(self, d1: int, d2: int, on_done=None) -> None:
        """굴러가는 연출 뒤 결과를 보여 주고 on_done()을 부른다."""
        self._result, self._on_done = (d1, d2), on_done
        self.move_badge.clear()
        self._frames_left = ROLL_FRAMES
        self._timer.start(FRAME_MS)

    def reset(self) -> None:
        self._timer.stop()
        for die in (self.die1, self.die2):
            die.tilt, die.jump = die.base_tilt, 0.0
            die.set_value(0)
        self.move_badge.clear()

    def set_roll_enabled(self, enabled: bool) -> None:
        self.roll_button.setEnabled(enabled)

    def set_end_mode(self, on: bool) -> None:
        """주사위를 굴린 뒤 투자를 할 수 있는 동안 큰 버튼을 '턴 마치기'로 바꾼다 (한 턴의 순서 7번)."""
        self.roll_button.setText("턴 마치기" if on else "주사위 굴리기!")
        self.roll_button.setProperty("role", "good" if on else "primary")
        self.roll_button.style().unpolish(self.roll_button)
        self.roll_button.style().polish(self.roll_button)

    def set_invest_enabled(self, enabled: bool) -> None:
        """투자 기회 턴에만 버튼이 보인다 (꺼진 버튼을 늘 보여 주지 않는다)."""
        self.invest_button.setEnabled(enabled)
        self.invest_button.setVisible(enabled)

    # ── 연출 ────────────────────────────────────────────────────
    def _frame(self) -> None:
        self._frames_left -= 1
        step = ROLL_FRAMES - self._frames_left
        if self._frames_left > 0:
            for i, die in enumerate((self.die1, self.die2)):
                die.value = random.randint(1, 6)
                die.tilt = random.uniform(-35, 35)
                die.jump = abs(math.sin((step + i * 2) * 0.9)) * 22 * (self._frames_left / ROLL_FRAMES)
                die.update()
            return
        self._timer.stop()
        for die, value in zip((self.die1, self.die2), self._result):
            die.tilt, die.jump = die.base_tilt, 0.0
            die.set_value(value)
        self.move_badge.pop(f"{sum(self._result)}칸!")
        callback, self._on_done = self._on_done, None
        if callback:
            QTimer.singleShot(260, callback)          # 배지가 튀어나오는 것을 본 뒤 말이 출발
