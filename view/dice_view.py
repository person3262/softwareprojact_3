"""
view/dice_view.py  —  DiceView: 주사위 2개 결과 출력 (FR-02-05) + 조작 버튼

  DiceView
   ├─ roll_button   "주사위 굴리기"   ← 클릭 감지는 Input이 한다 (View는 버튼만 제공)
   ├─ invest_button "투자하기"        ← 투자 가능한 턴에만 활성화 (FR-01-16)
   ├─ DieFace × 2                     ← 주사위 그림 (QPainter로 직접 그림, 이미지 파일 불필요)
   └─ sum_label     "합계: 7"
"""
from __future__ import annotations

import random

from PyQt5.QtCore import Qt, QRectF, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout

ROLL_FRAMES = 8      # 굴러가는 연출 프레임 수
FRAME_MS = 60        # 프레임 간격(ms) → 약 0.5초

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
    """주사위 한 개 그림"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0        # 0 = 아직 안 굴림(빈 주사위)
        self.setFixedSize(64, 64)

    def set_value(self, value: int) -> None:
        self.value = value
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(3, 3, self.width() - 6, self.height() - 6)
        p.setPen(QPen(QColor("#222222"), 2))
        p.setBrush(QBrush(QColor("white")))
        p.drawRoundedRect(rect, 10, 10)

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#222222")))
        step = rect.width() / 4
        r = rect.width() * 0.08
        for col, row in PIPS.get(self.value, []):
            p.drawEllipse(QPointF(rect.left() + step * (col + 1), rect.top() + step * (row + 1)), r, r)
        p.end()


class DiceView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.roll_button = QPushButton("주사위 굴리기")
        self.roll_button.setMinimumHeight(36)
        self.invest_button = QPushButton("투자하기")
        self.invest_button.setEnabled(False)

        self.die1, self.die2 = DieFace(), DieFace()
        self.sum_label = QLabel("합계: -")
        self.sum_label.setAlignment(Qt.AlignCenter)
        self.sum_label.setStyleSheet("font-size: 15px; font-weight: bold;")

        dice_row = QHBoxLayout()
        dice_row.addStretch(1)
        dice_row.addWidget(self.die1)
        dice_row.addWidget(self.die2)
        dice_row.addStretch(1)

        buttons = QHBoxLayout()
        buttons.addWidget(self.roll_button, 2)
        buttons.addWidget(self.invest_button, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(buttons)
        layout.addLayout(dice_row)
        layout.addWidget(self.sum_label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._frame)
        self._frames_left = 0
        self._result = (0, 0)
        self._on_done = None

    def show_result(self, d1: int, d2: int, on_done=None) -> None:
        """주사위가 잠깐 굴러가는 연출을 보여 준 뒤 d1, d2를 표시한다.
        숫자는 Model(Dice)이 정한 값 그대로 받는다. View는 화면 연출만 담당."""
        self._result = (d1, d2)
        self._on_done = on_done
        self._frames_left = ROLL_FRAMES
        self.sum_label.setText("굴리는 중…")
        self._timer.start(FRAME_MS)

    def _frame(self) -> None:
        if self._frames_left > 0:   # 연출용 무작위 눈 (게임 결과와 무관)
            self.die1.set_value(random.randint(1, 6))
            self.die2.set_value(random.randint(1, 6))
            self._frames_left -= 1
            return
        self._timer.stop()
        d1, d2 = self._result
        self.die1.set_value(d1)
        self.die2.set_value(d2)
        self.sum_label.setText(f"{d1} + {d2} = {d1 + d2}")
        callback, self._on_done = self._on_done, None
        if callback:
            callback()

    def set_roll_enabled(self, enabled: bool) -> None:
        self.roll_button.setEnabled(enabled)

    def set_invest_enabled(self, enabled: bool) -> None:
        self.invest_button.setEnabled(enabled)
