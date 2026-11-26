"""
view/dialogs/event.py  —  이벤트를 보여 주거나 하나를 고르게 하는 창

  EventDialog    행운·불행·황금열쇠·속보·정산 결과 카드 (FR-02-06)
                 불행이면 '행복 -50 → -41, 체력 34 덕분에 18% 덜 아팠어요'처럼 줄어든 값을 보여 준다.
  ChoiceDialog   선택 이벤트 (선택지 중 하나)  예) 지갑을 주웠다: 가진다 / 돌려준다
  ConfirmDialog  예/아니요  예) 불운→행운 변경권을 쓸까요? · 국가고시 재수할까요?
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath, QPolygonF
from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout, QSizePolicy

from common.adapter import read_event
from view import style
from view.painter_kit import draw_tile_icon
from view.widgets import title, quiet, button, chip, hbox
from view.dialogs.base import BaseDialog, big_label, effect_lines, effect_html

ICON_KIND = {"luck": "luck", "badluck": "badluck", "golden_key": "golden_key", "rest": "rest",
             "business": "coins", "invest": "coins", "gig": "paper", "artwork": "palette",
             "exam": "cap", "news": "start", "info": "start"}


class _Banner(QWidget):
    """카드 위쪽 그림 띠: 바탕색 + 큰 아이콘 (불행이면 빗줄기)"""

    def __init__(self, kind: str, bg: str, accent: str, parent=None):
        super().__init__(parent)
        self.kind, self.bg, self.accent = kind, QColor(bg), QColor(accent)
        self.setFixedHeight(130)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event) -> None:
        import math
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(2, 2, self.width() - 4, self.height() - 4)
        clip = QPainterPath()
        clip.addRoundedRect(rect, 18, 18)
        p.setClipPath(clip)
        p.fillRect(rect, self.bg)
        c = rect.center()
        if self.kind == "badluck":              # 빗줄기
            p.setPen(QPen(QColor(self.accent).lighter(130), 3, Qt.SolidLine, Qt.RoundCap))
            for i in range(30):
                x = (i * 37) % max(1, self.width())
                y = (i * 23) % max(1, self.height() - 16)
                p.drawLine(QPointF(x, y), QPointF(x - 5, y + 14))
        else:                                   # 햇살 무늬
            rays = QColor(self.accent)
            rays.setAlpha(45)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(rays))
            for i in range(14):
                a0 = math.pi * 2 * i / 14
                a1 = a0 + math.pi / 14
                far = max(rect.width(), rect.height())
                p.drawPolygon(QPolygonF([c, QPointF(c.x() + far * math.cos(a0), c.y() + far * math.sin(a0)),
                                         QPointF(c.x() + far * math.cos(a1), c.y() + far * math.sin(a1))]))
        p.setClipping(False)
        p.setPen(QPen(QColor(style.INK), 3))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(rect, 18, 18)
        # 가운데 흰 원 스티커 + 큰 아이콘
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(style.INK)))
        p.drawEllipse(c + QPointF(0, 5), 52, 52)
        p.setPen(QPen(QColor(style.INK), 3.5))
        p.setBrush(QBrush(QColor("white")))
        p.drawEllipse(c, 52, 52)
        size = 84
        icon = QRectF(c.x() - size / 2, c.y() - size / 2, size, size)
        draw_tile_icon(p, icon, ICON_KIND.get(self.kind, "luck"), self.accent)
        p.end()


class EventDialog(BaseDialog):
    """이벤트 카드: 머리말(단계·직업), 이름, 설명, 변화량, 피해 감소 설명"""

    def __init__(self, event, player_name: str = "", auto_close_ms: int = None, parent=None):
        super().__init__(parent, 480, "이벤트")
        e = read_event(event)
        head_text, bg, accent, ok_text = style.EVENT_STYLE.get(e.kind, style.EVENT_STYLE["info"])
        self.setWindowTitle(head_text)

        top = QHBoxLayout()
        label = e.stage_label or player_name
        if label:
            top.addWidget(chip(label, "white", style.INK, bold=True, size=12))
        top.addStretch(1)
        top.addWidget(title(head_text, 18, accent))
        self.body.addLayout(top)
        if e.kind not in ("news",):
            self.body.addWidget(_Banner(e.kind, bg, accent))
        name = big_label(e.name, 28 if e.kind != "news" else 22)
        self.body.addWidget(name)
        if e.description:
            self.body.addWidget(quiet(e.description, 13))

        # 변화량: 줄어들기 전 값이 있으면 '-50 → -41' 모양
        effects = QHBoxLayout()
        effects.setSpacing(8)
        reduced = e.base_money is not None or e.base_happiness is not None
        if reduced:
            if e.base_money is not None and e.base_money != 0:
                effects.addWidget(self._reduced_chip("돈", e.base_money, e.money, money=True))
            if e.base_happiness is not None and e.base_happiness != 0:
                effects.addWidget(self._reduced_chip("행복", e.base_happiness, e.happiness))
            for text, color in effect_lines(0, 0, e.stats):
                effects.addWidget(self._effect_chip(text, color))
        else:
            for text, color in effect_lines(e.money, e.happiness, e.stats):
                effects.addWidget(self._effect_chip(text, color))
        effects.addStretch(1)
        self.body.addLayout(effects)

        if e.reduce_stat and e.reduce_percent:
            note = QLabel(f"{e.reduce_stat} {e.reduce_value} 덕분에 {e.reduce_percent}% 덜 아팠어요")
            note.setStyleSheet(f"color: {style.darker(style.POOL, 140)}; font-size: 12px; font-weight: bold;")
            self.body.addWidget(note)
        for line in e.lines:
            self.body.addWidget(QLabel(line))
        if e.skip_turns:
            self.body.addWidget(QLabel(f"<b style='color:{style.BAD}'>다음 턴 {e.skip_turns}번 쉽니다.</b>"))

        ok = button(ok_text, role="primary", min_height=46)
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        self.body.addWidget(ok)
        self.auto_close(auto_close_ms)
        # 뜬 직후 연출: 좋은 일이면 색종이, 불행이면 흔들림
        good = e.kind in ("luck", "golden_key") or (e.kind in ("business", "invest", "gig", "artwork")
                                                     and (e.money > 0 or e.happiness > 0))
        self.after_show = "shake" if e.kind == "badluck" else "confetti" if good else ""

    @staticmethod
    def _effect_chip(text: str, color: str) -> QLabel:
        label = QLabel(text)
        label.setFont(style.title_font(18))
        label.setStyleSheet(f"color: {color}; background: white; border: 3px solid {style.INK};"
                            " border-radius: 13px; padding: 4px 12px;")
        return label

    @staticmethod
    def _reduced_chip(name: str, base: int, actual: int, money: bool = False) -> QLabel:
        fmt = style.format_money_delta if money else style.format_delta
        label = QLabel(f"{name}  <s style='color:#9AA0B4'>{fmt(base)}</s>  →  <b>{fmt(actual)}</b>")
        label.setFont(style.title_font(18))
        label.setStyleSheet(f"color: {style.BAD}; background: #FFE8EC; border: 3px solid {style.INK};"
                            " border-radius: 13px; padding: 4px 12px;")
        return label


class ChoiceDialog(BaseDialog):
    """선택 이벤트: 선택지 버튼 중 하나를 고른다.
    options는 문자열 목록이거나 이벤트 모양 dict 목록({"name", "money", "happiness", "stats"})"""

    def __init__(self, title_text: str, question: str, options, parent=None):
        super().__init__(parent, 460, title_text)
        self.selected_index = None
        self.body.addWidget(title(title_text, 16, style.TEXT_QUIET))
        self.body.addWidget(big_label(question, 24))
        for i, raw in enumerate(options):
            opt = read_event({"name": raw} if isinstance(raw, str) else raw)   # 문자열 선택지도 된다
            b = button(opt.name, role="primary" if i == 0 else "", min_height=42)
            b.clicked.connect(lambda _, idx=i: self._choose(idx))
            self.body.addWidget(b)
            if opt.money or opt.happiness or opt.stats:
                effect = QLabel(effect_html(opt.money, opt.happiness, opt.stats))
                effect.setAlignment(Qt.AlignCenter)
                self.body.addWidget(effect)

    def _choose(self, index: int) -> None:
        self.selected_index = index
        self.accept()


class ConfirmDialog(BaseDialog):
    """예/아니요 질문. answer = True / False"""

    def __init__(self, title_text: str, question: str, detail: str = "", yes_text: str = "네",
                 no_text: str = "아니요", parent=None):
        super().__init__(parent, 440, title_text)
        self.answer = False
        self.body.addWidget(title(title_text, 16, style.TEXT_QUIET))
        self.body.addWidget(big_label(question, 24))
        if detail:
            self.body.addWidget(quiet(detail, 13))
        no = button(no_text)
        yes = button(yes_text, role="primary")
        yes.setDefault(True)
        no.clicked.connect(self.reject)
        yes.clicked.connect(self._yes)
        self.body.addLayout(hbox(no, yes))

    def _yes(self) -> None:
        self.answer = True
        self.accept()
