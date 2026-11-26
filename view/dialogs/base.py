"""
view/dialogs/base.py  —  모든 대화창의 바탕 (BaseDialog) + 변화량 표시 도우미

BaseDialog
  - 테두리 없는 흰 스티커 카드 모양 창
  - 창이 떠 있는 동안 뒤의 메인 창을 어둡게 덮는다
  - 뜰 때 위에서 툭 떨어지며 나타난다. 좋은 결과면 색종이(celebrate), 나쁜 결과면 흔들림(shake)
  - 모달(exec_)이라 창이 닫힐 때까지 다음 코드가 기다린다
    → Controller에서 "값 = input.ask_job(...)" 처럼 한 줄로 쓸 수 있다.
  - Esc를 누르면 닫힌다 (취소/건너뛰기와 같다)
"""
from __future__ import annotations

import random

from PyQt5.QtCore import Qt, QTimer, QPointF, QVariantAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QColor, QPainter, QBrush
from PyQt5.QtWidgets import (QDialog, QFrame, QVBoxLayout, QWidget, QLabel, QGraphicsDropShadowEffect)

from common.constants import STAT_NAMES
from view import style


def effect_lines(money: int = 0, happiness: int = 0, stats: dict = None) -> list:
    """변화량을 [(문구, 색), ...]로 만든다. 예) [("돈 +300만원", 초록)]"""
    lines = []
    if money:
        lines.append((f"돈 {style.format_money_delta(money)}", style.delta_color(money)))
    if happiness:
        lines.append((f"행복 {style.format_delta(happiness)}", style.HAPPY if happiness > 0 else style.BAD))
    for name, v in (stats or {}).items():
        if v:
            lines.append((f"{name} {style.format_delta(v)}", style.delta_color(v)))
    return lines


def effect_html(money: int = 0, happiness: int = 0, stats: dict = None) -> str:
    parts = [f"<span style='color:{c}'><b>{t}</b></span>" for t, c in effect_lines(money, happiness, stats)]
    return "&nbsp;&nbsp;".join(parts) if parts else "변화 없음"


def stats_text(stats: dict) -> str:
    return " · ".join(f"{n} {stats.get(n, 0)}" for n in STAT_NAMES)


class _Shade(QWidget):
    """대화창 뒤의 메인 창을 어둡게 덮는 반투명 막"""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: rgba(35, 38, 74, 110);")
        self.setGeometry(parent.rect())
        self.show()
        self.raise_()


class Confetti(QWidget):
    """색종이: 위에서 흩뿌려져 떨어진다 (약 1.5초). 마우스 클릭은 통과시킨다."""

    COLORS = [style.CHERRY, style.SUN, style.LEAF, style.POOL, style.STORM, style.HAPPY]

    def __init__(self, parent: QWidget, count: int = 70):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setGeometry(parent.rect())
        w = max(1, self.width())
        rng = random.Random()
        self.bits = [[rng.uniform(0, w), rng.uniform(-60, 10), rng.uniform(-2.2, 2.2), rng.uniform(1.5, 4.5),
                      rng.uniform(0, 360), rng.uniform(-14, 14), rng.choice(self.COLORS), rng.choice((0, 1))]
                     for _ in range(count)]
        self.frames = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(30)
        self.show()
        self.raise_()

    def _tick(self) -> None:
        self.frames += 1
        for b in self.bits:
            b[0] += b[2]
            b[1] += b[3]
            b[3] += 0.12                    # 중력
            b[4] += b[5]
        if self.frames > 55:
            self.timer.stop()
            self.deleteLater()
            return
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setOpacity(1.0 if self.frames < 38 else max(0.0, 1 - (self.frames - 38) / 17))
        p.setPen(Qt.NoPen)
        for x, y, _, _, angle, _, color, shape in self.bits:
            p.save()
            p.translate(x, y)
            p.rotate(angle)
            p.setBrush(QBrush(QColor(color)))
            if shape:
                p.drawRect(-5, -3, 10, 6)
            else:
                p.drawEllipse(QPointF(0, 0), 3.5, 3.5)
            p.restore()
        p.end()


class BaseDialog(QDialog):
    """흰 카드 모양 대화창. 내용은 self.body(QVBoxLayout)에 넣는다."""

    def __init__(self, parent=None, width: int = 520, title: str = "인생마불"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.card = QFrame(self)
        self.card.setObjectName("dialogcard")
        self.card.setStyleSheet(f"QFrame#dialogcard {{ background: white; border: 4px solid {style.INK};"
                                " border-radius: 26px; }")
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(0)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(style.INK))
        self.card.setGraphicsEffect(shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 16)
        outer.addWidget(self.card)
        self.body = QVBoxLayout(self.card)
        self.body.setContentsMargins(26, 22, 26, 22)
        self.body.setSpacing(10)
        self.setMinimumWidth(width)
        self._shade = None
        self.after_show = ""                 # "confetti" / "shake" / "" — 뜬 직후 연출
        self._target = None
        self._entrance = QVariantAnimation(self)
        self._entrance.setDuration(320)
        self._entrance.setStartValue(0.0)
        self._entrance.setEndValue(1.0)
        self._entrance.setEasingCurve(QEasingCurve.OutBack)
        self._entrance.valueChanged.connect(self._on_entrance)
        self._entrance.finished.connect(self._after_entrance)

    # ── 연출 ────────────────────────────────────────────────────
    def _on_entrance(self, value) -> None:
        t = float(value)
        self.setWindowOpacity(max(0.0, min(1.0, t * 1.6)))
        if self._target is not None:
            self.move(self._target.x(), int(self._target.y() - 36 * (1 - t)))

    def _after_entrance(self) -> None:
        if self.after_show == "confetti":
            self.celebrate()
        elif self.after_show == "shake":
            self.shake()

    def celebrate(self) -> None:
        """색종이를 뿌린다 (행운, 대박, 합격, 결과 발표)"""
        Confetti(self)

    def shake(self) -> None:
        """좌우로 흔든다 (불행)"""
        origin = self.pos()
        anim = QVariantAnimation(self)
        anim.setDuration(360)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.valueChanged.connect(lambda v: self.move(origin + QPoint(int(9 * (1 - v) * (1 if int(v * 8) % 2 else -1)), 0)))
        anim.finished.connect(lambda: self.move(origin))
        anim.start()

    def auto_close(self, ms: int) -> None:
        """NPC 차례에는 잠깐 보여 주고 자동으로 닫는다"""
        if ms:
            QTimer.singleShot(ms, self.accept)

    def exec_(self) -> int:
        host = self.parentWidget().window() if self.parentWidget() is not None else None
        if host is not None and host.isVisible():
            self._shade = _Shade(host)
            self.adjustSize()
            geo = host.geometry()
            self._target = QPoint(geo.center().x() - self.width() // 2, geo.center().y() - self.height() // 2)
            self.move(self._target)
        self.setWindowOpacity(0.0)
        self._entrance.start()
        try:
            return super().exec_()
        finally:
            if self._shade is not None:
                self._shade.deleteLater()
                self._shade = None


def big_label(text: str, size: int = 26, color: str = style.INK, wrap: bool = True) -> QLabel:
    label = QLabel(text)
    label.setFont(style.title_font(size))
    label.setStyleSheet(f"color: {color};")
    label.setWordWrap(wrap)
    return label
