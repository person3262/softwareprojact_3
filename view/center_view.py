"""
view/center_view.py  —  보드 가운데 영역

  CenterPanel
   ├─ LogoTiles      "인생마불" 글자 스티커 + "응애에서 은퇴까지"
   ├─ LifeMapView    인생 지도: 다섯 단계 정류장 위에 플레이어 얼굴 (FR-02-13)
   ├─ TurnBanner     리본 배너 "정민의 차례!" (차례가 바뀌면 옆에서 미끄러져 들어온다)
   ├─ DiceView       주사위 · "7칸!" · 굴리기 버튼 · 투자 버튼
   ├─ NewsTicker     속보 띠: 대박·유행 소식이 흘러간다 (FR-02-13)
   └─ FloatingText   매 턴 수입 "+700만원 / 행복 +7"이 툭 튀어나왔다가 떠오르며 사라진다 (FR-02-10)
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer, QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFontMetrics, QPolygonF
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

from common.constants import STAGES
from common.adapter import read_player
from view import style
from view.painter_kit import draw_face, draw_sticker, draw_coin, draw_heart
from view.dice_view import DiceView

TICKER_MS = 30            # 속보 띠가 한 번 움직이는 간격
FLOAT_MS = 1500           # 수입 숫자가 떠 있는 시간
FLOAT_STEP_MS = 30


def player_lap_in_stage(info) -> int:
    """상태창·배너의 '성년기 3바퀴'는 지금까지 완주한 바퀴 수(누적)다. 0바퀴면 숫자를 빼고 단계만 쓴다."""
    return max(0, info.lap)


def stage_text(info) -> str:
    laps = player_lap_in_stage(info)
    return f"{info.stage} {laps}바퀴" if laps else info.stage


def outlined_text(p, x: float, y: float, text: str, font, fill, outline=style.INK, width: float = 5) -> float:
    """잉크 테두리가 있는 글자 (스티커 글씨). 그린 글자 너비를 돌려준다."""
    path = QPainterPath()
    path.addText(QPointF(x, y), font, text)
    p.setPen(QPen(QColor(outline), width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(fill)))
    p.drawPath(path)
    return QFontMetrics(font).horizontalAdvance(text)


class LogoTiles(QWidget):
    """'인생마불' 네 글자를 색깔 스티커 타일로, 아래에 한 줄"""

    COLORS = [style.CHERRY, style.SUN, style.LEAF, style.POOL]
    TILTS = [-6, 4, -3, 6]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(92)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        size, gap = 52, 10
        total = size * 4 + gap * 3
        x0 = (self.width() - total) / 2
        font = style.title_font(36)
        for i, (ch, color, tilt) in enumerate(zip("인생마불", self.COLORS, self.TILTS)):
            p.save()
            p.translate(x0 + i * (size + gap) + size / 2, 8 + size / 2)
            p.rotate(tilt)
            draw_sticker(p, QRectF(-size / 2, -size / 2, size, size), color, radius=13, outline=3.5, shadow=5)
            text_color = style.INK if color == style.SUN else "white"
            fm = QFontMetrics(font)
            w = fm.horizontalAdvance(ch)
            outlined_text(p, -w / 2, fm.ascent() / 2 - 3, ch, font, text_color, style.INK, 0 if text_color == style.INK else 4)
            p.restore()
        p.setPen(QColor(style.TEXT_QUIET))
        p.setFont(style.title_font(15))
        p.drawText(QRectF(0, size + 22, self.width(), 22), Qt.AlignCenter, "응애에서 은퇴까지, 주사위로 사는 인생")
        p.end()


class LifeMapView(QWidget):
    """인생 지도: 유아기 → 노년기 구불구불한 길, 정류장 위에 플레이어 얼굴"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(108)
        self.players = []          # [(PlayerInfo, 색)]
        self.current_id = None

    def set_players(self, players, colors: dict) -> None:
        self.players = [(read_player(p), colors.get(read_player(p).id, QColor("#999"))) for p in players]
        self.update()

    def set_current(self, player_id) -> None:
        self.current_id = player_id
        self.update()

    def _stop(self, i: int) -> QPointF:
        w = self.width()
        x = 34 + (w - 68) * i / 4
        y = 70 + (-10 if i % 2 else 8)
        return QPointF(x, y)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        stops = [self._stop(i) for i in range(5)]
        road = QPainterPath(stops[0])
        for a, b in zip(stops, stops[1:]):
            mid = (a.x() + b.x()) / 2
            road.cubicTo(QPointF(mid, a.y()), QPointF(mid, b.y()), b)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(style.INK), 16, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(road)
        p.setPen(QPen(QColor("#FFE9A8"), 10, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(road)
        dash = QPen(QColor("white"), 2.5, Qt.DashLine, Qt.RoundCap)
        dash.setDashPattern([3, 3])
        p.setPen(dash)
        p.drawPath(road)

        p.setFont(style.title_font(13))
        for i, c in enumerate(stops):
            p.setPen(QPen(QColor(style.INK), 3))
            p.setBrush(QBrush(QColor(style.STAGE_COLORS[i])))
            p.drawEllipse(c, 11, 11)
            p.setPen(QColor(style.INK))
            p.drawText(QRectF(c.x() - 40, c.y() + 12, 80, 18), Qt.AlignCenter, STAGES[i])

        # 같은 단계에 있는 사람끼리 나란히. 지금 차례인 사람은 크게
        groups = {}
        for info, color in self.players:
            groups.setdefault(min(4, info.stage_index), []).append((info, color))
        for stage, members in groups.items():
            c = stops[stage]
            n = len(members)
            for k, (info, color) in enumerate(members):
                big = info.id == self.current_id
                size = 34 if big else 26
                x = c.x() + (k - (n - 1) / 2) * 22
                rect = QRectF(x - size / 2, c.y() - 16 - size, size, size)
                draw_face(p, rect, info.character, color, info.is_npc)
        p.end()


class TurnBanner(QWidget):
    """리본 배너 '정민의 차례!' — 플레이어 색, 차례가 바뀌면 옆에서 미끄러져 들어온다"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.info = None
        self.color = QColor(style.CARD_LINE)
        self.title_text = "게임 준비 중"
        self.sub_text = ""
        self.slide = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(380)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.OutBack)
        self.anim.valueChanged.connect(self._on_slide)

    def _on_slide(self, value) -> None:
        self.slide = float(value)
        self.update()

    def set_player(self, info, color: QColor) -> None:
        changed = self.info is None or self.info.id != info.id
        self.info, self.color = info, QColor(color)
        self.title_text = f"{info.name}의 차례!"
        job = info.job or ("의대생" if info.job_state == "student" else "")
        self.sub_text = "  ".join(x for x in (info.character, job, stage_text(info)) if x)
        if changed and self.isVisible():
            self.anim.stop()
            self.anim.start()
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = min(self.width() - 20, 420)
        x0 = (self.width() - w) / 2 - self.slide * 60
        p.setOpacity(1 - min(1.0, self.slide))
        top, h, notch = 8, 52, 16
        ribbon = QPolygonF([QPointF(x0, top), QPointF(x0 + w, top), QPointF(x0 + w - notch, top + h / 2),
                            QPointF(x0 + w, top + h), QPointF(x0, top + h), QPointF(x0 + notch, top + h / 2)])
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(style.INK)))
        p.drawPolygon(ribbon.translated(0, 5))
        p.setPen(QPen(QColor(style.INK), 3.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(QBrush(self.color))
        p.drawPolygon(ribbon)
        face = QRectF(x0 + 26, top + 4, h - 8, h - 8)
        if self.info is not None:
            draw_face(p, face, self.info.character, self.color.lighter(125), self.info.is_npc)
        text_x = face.right() + 12 if self.info is not None else x0 + 40
        font = style.title_font(24)
        outlined_text(p, text_x, top + 30, self.title_text, font, "white", style.INK, 5)
        if self.sub_text:
            p.setPen(QColor("white"))
            p.setFont(style.title_font(13))
            p.drawText(QRectF(text_x, top + 33, w - (text_x - x0) - 20, 18), Qt.AlignLeft | Qt.AlignVCenter,
                       self.sub_text)
        p.end()


class NewsTicker(QWidget):
    """속보 띠: 체리색 '속보' 딱지 + 흘러가는 소식"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(42)
        self.news = []
        self.offset = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def add_news(self, text: str) -> None:
        self.news.insert(0, text)
        del self.news[5:]
        self.offset = 0.0
        if not self._timer.isActive():
            self._timer.start(TICKER_MS)
        self.update()

    def text(self) -> str:
        return "        ".join(self.news)

    def _tick(self) -> None:
        self.offset += 1.2
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(2, 2, self.width() - 4, self.height() - 9)
        draw_sticker(p, rect, style.PAPER, radius=rect.height() / 2, outline=3, shadow=4)
        tab = QRectF(rect.left(), rect.top(), 70, rect.height())
        clip = QPainterPath()
        clip.addRoundedRect(rect.adjusted(1.5, 1.5, -1.5, -1.5), rect.height() / 2, rect.height() / 2)
        p.setClipPath(clip)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(style.CHERRY)))
        p.drawRect(tab)
        p.setPen(QPen(QColor(style.INK), 3))
        p.drawLine(QPointF(tab.right(), rect.top()), QPointF(tab.right(), rect.bottom()))
        p.setFont(style.title_font(17))
        p.setPen(QColor("white"))
        p.drawText(tab, Qt.AlignCenter, "속보")
        # 흘러가는 글자
        lane = QRectF(tab.right() + 10, rect.top(), rect.right() - tab.right() - 22, rect.height())
        p.setClipRect(lane)
        p.setFont(style.title_font(15))
        p.setPen(QColor(style.INK))
        text = self.text() or "오늘의 인생 소식을 기다리는 중"
        width = QFontMetrics(p.font()).horizontalAdvance(text) + 80
        x = lane.left() - (self.offset % width) if width > lane.width() else lane.left()
        p.drawText(QRectF(x, lane.top(), width, lane.height()), Qt.AlignLeft | Qt.AlignVCenter, text)
        if width > lane.width():
            p.drawText(QRectF(x + width, lane.top(), width, lane.height()), Qt.AlignLeft | Qt.AlignVCenter, text)
        p.end()


class FloatingText(QWidget):
    """'+700만원 / 행복 +7'이 툭 튀어나왔다가 위로 떠오르며 사라진다. 마우스 클릭은 통과시킨다."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.lines = []               # [(문구, 색, 크기, 아이콘)]
        self.elapsed = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.hide()

    def show_lines(self, lines) -> None:
        self.lines = [tuple(line) + ("",) * (4 - len(line)) for line in lines]
        self.elapsed = 0
        self.show()
        self.raise_()
        self._timer.start(FLOAT_STEP_MS)
        self.update()

    def _tick(self) -> None:
        self.elapsed += FLOAT_STEP_MS
        if self.elapsed >= FLOAT_MS:
            self._timer.stop()
            self.hide()
        self.update()

    def paintEvent(self, event) -> None:
        if not self.lines:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t = self.elapsed / FLOAT_MS
        pop = QEasingCurve(QEasingCurve.OutBack).valueForProgress(min(1.0, t / 0.22))
        scale = 0.5 + 0.5 * pop
        alpha = 1.0 if t < 0.65 else max(0.0, 1 - (t - 0.65) / 0.35)
        rise = 34 * max(0.0, t - 0.25)
        p.setOpacity(alpha)
        cx, y = self.width() * 0.5, self.height() * 0.6 - rise
        for text, color, size, icon in self.lines:
            font = style.title_font(size)
            fm = QFontMetrics(font)
            icon_w = size * 0.9 if icon else 0
            total = fm.horizontalAdvance(text) + icon_w + (8 if icon else 0)
            p.save()
            p.translate(cx, y)
            p.scale(scale, scale)
            x = -total / 2
            if icon == "coin":
                draw_coin(p, QRectF(x, -size * 0.78, icon_w, icon_w))
            elif icon == "heart":
                draw_heart(p, QRectF(x, -size * 0.78, icon_w, icon_w))
            x += icon_w + (8 if icon else 0)
            outlined_text(p, x, 0, text, font, color, style.INK, 7)
            p.restore()
            y += size + 10
        p.end()


class CenterPanel(QWidget):
    """보드 가운데 6×6 칸 영역 전체. BoardView가 크기에 맞춰 위치를 잡아 준다."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logo = LogoTiles()
        self.life_map = LifeMapView()
        self.banner = TurnBanner()
        self.dice_view = DiceView()
        self.ticker = NewsTicker()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 12)
        layout.setSpacing(4)
        layout.addWidget(self.logo)
        layout.addWidget(self.life_map)
        layout.addWidget(self.banner)
        layout.addStretch(1)
        layout.addWidget(self.dice_view)
        layout.addStretch(1)
        layout.addWidget(self.ticker)

        self.floating = FloatingText(self)

    def resizeEvent(self, event) -> None:
        self.floating.setGeometry(self.rect())
        super().resizeEvent(event)

    def show_income(self, money: int, happiness: int) -> None:
        lines = []
        if money:
            lines.append((style.format_money_delta(money), style.LEAF if money > 0 else style.BAD, 40, "coin"))
        if happiness:
            lines.append((f"행복 {style.format_delta(happiness)}", style.HAPPY if happiness > 0 else style.BAD,
                          26, "heart"))
        if lines:
            self.floating.show_lines(lines)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(style.BOARD_BG)))
        p.drawRoundedRect(rect, 20, 20)
        p.setBrush(QBrush(QColor(style.BOARD_DOT)))      # 점무늬
        step = 22
        y = rect.top() + step / 2
        row = 0
        while y < rect.bottom():
            x = rect.left() + step / 2 + (step / 2 if row % 2 else 0)
            while x < rect.right():
                p.drawEllipse(QPointF(x, y), 1.6, 1.6)
                x += step
            y += step
            row += 1
        p.end()
