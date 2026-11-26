"""
view/sky_view.py  —  SkyBackground: 창 전체 바탕 하늘 ("인생은 하루")

지금 차례인 사람의 인생 단계에 따라 하늘이 바뀐다.
  유아기 새벽 → 청년기 아침 → 성년기 한낮 → 중년기 노을 → 노년기 밤(달과 별)
차례가 바뀌어 단계가 달라질 때만 0.7초 동안 천천히 섞이며 바뀐다. 그 밖에는 움직이지 않는다.
"""
from __future__ import annotations

import random

from PyQt5.QtCore import Qt, QPointF, QRectF, QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QBrush, QPainterPath, QPen
from PyQt5.QtWidgets import QWidget

from view import style

# 해·달 위치 (창 너비·높이에 대한 비율)와 크기, 색
# 보드와 상태창 사이·가장자리처럼 가려지지 않는 곳에 둔다
CELESTIAL = [
    (0.015, 0.70, 50, "#FFE1EC", "#FF9DC0"),    # 새벽: 왼쪽 아래에서 떠오르는 분홍 해
    (0.015, 0.22, 52, "#FFF6C9", "#FFD43B"),    # 아침: 왼쪽 위
    (0.40, 0.0, 64, "#FFFBE0", "#FFD43B"),      # 한낮: 보드 위로 머리를 내민 해
    (0.70, 0.62, 58, "#FFE3B8", "#FF8F3D"),     # 노을: 보드와 상태창 사이로 지는 해
    (0.70, 0.10, 42, "#FFFFFF", "#E8E4FF"),     # 밤: 달
]


class SkyBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage, self.previous, self.t = 1, 1, 1.0
        rng = random.Random(7)                                   # 별 자리는 늘 같게
        self.stars = [(rng.random(), rng.random() * 0.55, rng.choice((1.2, 1.6, 2.2))) for _ in range(70)]
        self.clouds = [(0.07, 0.08, 1.0), (0.34, 0.03, 0.75), (0.63, 0.12, 0.9), (0.93, 0.05, 0.7)]
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(700)
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._on_step)

    def set_stage(self, stage: int, animate: bool = True) -> None:
        stage = max(0, min(4, int(stage)))
        if stage == self.stage and self.t >= 1.0:
            return
        self.previous, self.stage = self.stage, stage
        if animate and self.isVisible():
            self.t = 0.0
            self.anim.stop()
            self.anim.start()
        else:
            self.t = 1.0
            self.update()

    def _on_step(self, value) -> None:
        self.t = float(value)
        self.update()

    # ── 그리기 ──────────────────────────────────────────────────
    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        a, b = style.STAGE_SKIES[self.previous], style.STAGE_SKIES[self.stage]
        top, bottom = style.mix(a[0], b[0], self.t), style.mix(a[1], b[1], self.t)
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, top)
        grad.setColorAt(1, bottom)
        p.fillRect(self.rect(), QBrush(grad))

        night = (1 - self.t) * (self.previous == 4) + self.t * (self.stage == 4)
        if night > 0:
            self._stars(p, w, h, night)
        for stage, alpha in ((self.previous, 1 - self.t), (self.stage, self.t)):
            if alpha > 0.01:
                self._celestial(p, w, h, stage, alpha)
        self._clouds(p, w, h, 1 - night * 0.75)
        self._hills(p, w, h, style.mix(style.STAGE_HILLS[self.previous], style.STAGE_HILLS[self.stage], self.t))
        p.end()

    def _stars(self, p, w, h, alpha) -> None:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, int(220 * alpha)))
        for x, y, r in self.stars:
            p.drawEllipse(QPointF(x * w, y * h), r, r)

    def _celestial(self, p, w, h, stage, alpha) -> None:
        fx, fy, radius, core, glow = CELESTIAL[stage]
        c = QPointF(fx * w, fy * h)
        p.save()
        p.setOpacity(alpha)
        p.setPen(Qt.NoPen)
        halo = QColor(glow)
        for i, scale in enumerate((2.2, 1.6)):
            halo.setAlpha(40 + i * 30)
            p.setBrush(halo)
            p.drawEllipse(c, radius * scale, radius * scale)
        p.setBrush(QColor(core))
        p.setPen(QPen(QColor(style.INK), 3))
        p.drawEllipse(c, radius, radius)
        if stage == 4:                                         # 달 무늬
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#DCD6F7"))
            for dx, dy, r in ((-0.3, -0.2, 0.18), (0.25, 0.15, 0.22), (-0.1, 0.38, 0.12)):
                p.drawEllipse(QPointF(c.x() + dx * radius, c.y() + dy * radius), r * radius, r * radius)
        p.restore()

    def _clouds(self, p, w, h, alpha) -> None:
        p.save()
        p.setOpacity(max(0.0, min(1.0, alpha)))
        for fx, fy, scale in self.clouds:
            s = 70 * scale
            x, y = fx * w, fy * h + 30
            path = QPainterPath()
            path.addEllipse(QPointF(x - s * 0.5, y + s * 0.12), s * 0.42, s * 0.3)
            path.addEllipse(QPointF(x, y - s * 0.05), s * 0.5, s * 0.42)
            path.addEllipse(QPointF(x + s * 0.55, y + s * 0.1), s * 0.38, s * 0.3)
            path.addRoundedRect(QRectF(x - s * 0.9, y + s * 0.05, s * 1.85, s * 0.38), s * 0.19, s * 0.19)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 215))
            p.drawPath(path.simplified())
        p.restore()

    def _hills(self, p, w, h, color: QColor) -> None:
        base = h * 0.84
        back = QPainterPath(QPointF(0, h))
        back.lineTo(0, base)
        back.cubicTo(w * 0.18, base - 70, w * 0.32, base - 20, w * 0.5, base - 40)
        back.cubicTo(w * 0.68, base - 60, w * 0.82, base - 10, w, base - 50)
        back.lineTo(w, h)
        front = QPainterPath(QPointF(0, h))
        front.lineTo(0, base + 40)
        front.cubicTo(w * 0.25, base - 10, w * 0.45, base + 60, w * 0.7, base + 20)
        front.cubicTo(w * 0.85, base, w * 0.95, base + 30, w, base + 10)
        front.lineTo(w, h)
        p.setPen(QPen(QColor(style.INK), 3))
        p.setBrush(color.lighter(112))
        p.drawPath(back)
        p.setBrush(color)
        p.drawPath(front)
