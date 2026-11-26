"""
view/widgets.py  —  여러 화면에서 같이 쓰는 작은 위젯과 만들기 함수

  chip()          둥근 이름표 ("범생이", "의사", "성년기 3바퀴")
  card_frame()    스티커 카드 (흰 바탕 + 잉크 테두리 + 번지지 않는 그림자)
  title()         주아체 제목 글자
  button()        버튼 (role="primary" 햇빛 노랑 / "good" 초록 / 기본 흰색)
  StatBar         "지력 ▬▬▬▬ 62" 능력치 막대 한 줄
  CountLabel      숫자가 바뀔 때 0.5초 동안 세어 올라가는(내려가는) 글자
  hbox() / vbox() 여백을 줄인 레이아웃
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QRectF, QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtWidgets import (QLabel, QFrame, QPushButton, QWidget, QHBoxLayout, QVBoxLayout,
                             QSizePolicy, QGraphicsDropShadowEffect)

from view import style

STAT_COLORS = {"지력": style.POOL, "체력": style.CHERRY, "센스": style.GOLD}


def chip(text: str, bg: str = "#EEF1F8", fg: str = "#4A5072", bold: bool = False, size: int = 11) -> QLabel:
    label = QLabel(text)
    set_chip(label, text, bg, fg, bold, size)
    label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    return label


def set_chip(label: QLabel, text: str, bg: str, fg: str, bold: bool = False, size: int = 11) -> None:
    weight = "bold" if bold else "normal"
    label.setText(text)
    label.setStyleSheet(f"background: {bg}; color: {fg}; border-radius: 10px; padding: 2px 9px;"
                        f" font-size: {size}px; font-weight: {weight};")


def sticker_shadow(widget: QWidget, offset: int = 5, color: str = style.INK) -> None:
    """번지지 않는 그림자 (스티커가 판 위에 붙은 느낌)"""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(0)
    effect.setOffset(0, offset)
    effect.setColor(QColor(color))
    widget.setGraphicsEffect(effect)


def card_frame(name: str = "card", border: str = style.INK, width: int = 3, bg: str = style.CARD_BG,
               radius: int = 16, shadow: bool = True) -> QFrame:
    frame = QFrame()
    frame.setObjectName(name)
    set_card_border(frame, border, width, bg, radius)
    if shadow:
        sticker_shadow(frame, 4)
    return frame


def set_card_border(frame: QFrame, border: str, width: int = 3, bg: str = style.CARD_BG, radius: int = 16) -> None:
    name = frame.objectName()
    frame.setStyleSheet(f"QFrame#{name} {{ background: {bg}; border: {width}px solid {border};"
                        f" border-radius: {radius}px; }}")


def title(text: str, size: int = 22, color: str = style.INK) -> QLabel:
    """주아체 제목"""
    label = QLabel(text)
    label.setFont(style.title_font(size))
    label.setStyleSheet(f"color: {color};")
    return label


def quiet(text: str, size: int = 12) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(f"color: {style.TEXT_QUIET}; font-size: {size}px;")
    label.setWordWrap(True)
    return label


def button(text: str, role: str = "", min_height: int = 40) -> QPushButton:
    b = QPushButton(text)
    if role:
        b.setProperty("role", role)
    b.setMinimumHeight(min_height + 4)            # 아래쪽 두꺼운 테두리만큼 더
    b.setCursor(Qt.PointingHandCursor)
    b.setFont(style.title_font(17 if min_height >= 40 else 14))
    return b


def hbox(*widgets, spacing: int = 6, margins=(0, 0, 0, 0)) -> QHBoxLayout:
    box = QHBoxLayout()
    box.setSpacing(spacing)
    box.setContentsMargins(*margins)
    for w in widgets:
        if w == "stretch":
            box.addStretch(1)
        elif isinstance(w, QWidget):
            box.addWidget(w)
        else:
            box.addLayout(w)
    return box


def vbox(*widgets, spacing: int = 6, margins=(0, 0, 0, 0)) -> QVBoxLayout:
    box = QVBoxLayout()
    box.setSpacing(spacing)
    box.setContentsMargins(*margins)
    for w in widgets:
        if w == "stretch":
            box.addStretch(1)
        elif isinstance(w, QWidget):
            box.addWidget(w)
        else:
            box.addLayout(w)
    return box


class Bar(QWidget):
    """잉크 테두리가 있는 둥근 막대 하나 (0 ~ maximum)"""

    def __init__(self, color: str, maximum: int = 100, height: int = 12, parent=None):
        super().__init__(parent)
        self.color, self.maximum, self.value = QColor(color), max(1, maximum), 0
        self.setFixedHeight(height)
        self.setMinimumWidth(30)

    def set_value(self, value: int) -> None:
        self.value = max(0, min(self.maximum, int(value)))
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        h = self.height() - 2
        outer = QRectF(1, 1, self.width() - 2, h)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#E9ECF6")))
        p.drawRoundedRect(outer, h / 2, h / 2)
        w = outer.width() * self.value / self.maximum
        if w > 0:
            p.setBrush(QBrush(self.color))
            p.drawRoundedRect(QRectF(1, 1, max(h, w), h), h / 2, h / 2)
            p.setBrush(QBrush(QColor(255, 255, 255, 90)))          # 윗부분 반짝임
            p.drawRoundedRect(QRectF(4, 3, max(h, w) - 6, h * 0.28), 2, 2)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(style.INK), 2))
        p.drawRoundedRect(outer, h / 2, h / 2)
        p.end()


class StatBar(QWidget):
    """'지력 ▬▬▬ 62' 한 묶음"""

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        color = STAT_COLORS.get(name, "#888888")
        self.label = QLabel(name)
        self.label.setFont(style.title_font(13))
        self.label.setStyleSheet(f"color: {style.darker(color, 125)};")
        self.bar = Bar(color)
        self.number = QLabel("0")
        self.number.setFont(style.title_font(13))
        self.number.setStyleSheet(f"color: {style.INK};")
        self.number.setMinimumWidth(22)
        self.number.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.label)
        layout.addWidget(self.bar, 1)
        layout.addWidget(self.number)

    def set_value(self, value: int) -> None:
        self.bar.set_value(value)
        self.number.setText(str(value))


class CountLabel(QLabel):
    """숫자가 바뀌면 0.5초 동안 세면서 바뀐다 (돈이 들어오는 느낌). formatter로 글자 모양을 정한다."""

    def __init__(self, formatter=str, parent=None):
        super().__init__(parent)
        self.formatter = formatter
        self.value = None
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(500)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.valueChanged.connect(lambda v: self.setText(self.formatter(int(v))))

    def set_value(self, value: int, animate: bool = True) -> None:
        value = int(value)
        if self.value is None or not animate or value == self.value or not self.isVisible():
            self.anim.stop()
            self.value = value
            self.setText(self.formatter(value))
            return
        self.anim.stop()
        self.anim.setStartValue(self.value)
        self.anim.setEndValue(value)
        self.value = value
        self.anim.start()
