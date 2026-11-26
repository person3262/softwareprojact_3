"""
view/painter_kit.py  —  QPainter로 직접 그리는 그림 모음 (이미지 파일 없이)

  draw_face()       캐릭터 얼굴: 범생이(안경) · 운동부(머리띠) · 감성러(베레모) · 평범이 · NPC(로봇)
  draw_tile_icon()  칸·카드 아이콘: 클로버 · 먹구름 · 열쇠 · 자물쇠 · 달 · 화살표 · 동전 · 의뢰서 · 팔레트 · 학사모
  draw_coin() / draw_heart() / draw_crown()
  draw_sticker()    스티커 모양 상자: 잉크 테두리 + 번지지 않는 그림자 (칸·주사위·배너가 같이 쓴다)
  draw_burst()      별 모양 배지 ("7칸!")

그림 파일을 쓰지 않으니 팀원 PC에서도 경로 문제 없이 똑같이 보인다.
모든 함수는 (painter, 영역 QRectF, ...) 모양이라 어디서든 같은 방법으로 부른다.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QColor, QPen, QBrush, QPainterPath, QPolygonF
from PyQt5.QtWidgets import QWidget, QSizePolicy

SKIN = QColor("#FFE1C4")
HAIR = QColor("#3B2F2F")
INK = QColor("#23264A")
BLUSH = QColor(255, 140, 150, 120)


def _pen(color, width: float) -> QPen:
    pen = QPen(QColor(color), width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


# ══════════════════════════════════════════════════════════
# 얼굴
# ══════════════════════════════════════════════════════════
def draw_face(p, rect: QRectF, character: str = "", color=None, npc: bool = False,
              ring: bool = True) -> None:
    """정사각형 rect 안에 동그란 얼굴을 그린다. color = 플레이어 색(바탕 원)"""
    p.save()
    p.setRenderHint(p.Antialiasing)
    s = min(rect.width(), rect.height())
    c = rect.center()
    r = s / 2
    bg = QColor(color) if color is not None else QColor("#CCCCCC")

    # 바탕 원 (플레이어 색) + 잉크 테두리
    p.setPen(_pen(INK, max(1.5, s * 0.06)) if ring else Qt.NoPen)
    p.setBrush(QBrush(bg))
    p.drawEllipse(c, r * 0.96, r * 0.96)

    if npc or character in ("NPC", "로봇"):
        _draw_robot(p, c, r)
    else:
        _draw_person(p, c, r, character)
    p.restore()


def _draw_person(p, c: QPointF, r: float, character: str) -> None:
    fr = r * 0.62                                   # 얼굴 반지름
    fc = QPointF(c.x(), c.y() + r * 0.08)

    # 뒷머리 (감성러는 단발)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(HAIR))
    if character == "감성러":
        p.drawRoundedRect(QRectF(fc.x() - fr * 1.12, fc.y() - fr * 1.0, fr * 2.24, fr * 1.75), fr * 0.7, fr * 0.7)

    # 얼굴
    p.setPen(_pen(INK, max(1.0, r * 0.05)))
    p.setBrush(QBrush(SKIN))
    p.drawEllipse(fc, fr, fr)

    # 앞머리
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(HAIR))
    hair = QPainterPath()
    if character == "운동부":                         # 짧은 삐죽 머리
        hair.moveTo(fc.x() - fr, fc.y() - fr * 0.25)
        for i in range(6):
            x = fc.x() - fr + (i + 0.5) * fr * 2 / 6
            hair.lineTo(x, fc.y() - fr * 1.22)
            hair.lineTo(x + fr * 2 / 12, fc.y() - fr * 0.75)
        hair.lineTo(fc.x() + fr, fc.y() - fr * 0.25)
        hair.arcTo(QRectF(fc.x() - fr, fc.y() - fr, fr * 2, fr * 2), 0, 180)
    else:                                            # 가르마 앞머리
        hair.moveTo(fc.x() - fr, fc.y())
        hair.arcTo(QRectF(fc.x() - fr, fc.y() - fr, fr * 2, fr * 2), 180, -180)
        hair.lineTo(fc.x() + fr * 0.95, fc.y() - fr * 0.15)
        hair.quadTo(fc.x() + fr * 0.2, fc.y() - fr * 0.55, fc.x() - fr * 0.15, fc.y() - fr * 0.35)
        hair.quadTo(fc.x() - fr * 0.6, fc.y() - fr * 0.2, fc.x() - fr * 0.95, fc.y() + fr * 0.05)
    hair.closeSubpath()
    p.drawPath(hair)

    # 눈 · 볼 · 입
    eye_y = fc.y() + fr * 0.12
    p.setBrush(QBrush(INK))
    for dx in (-0.36, 0.36):
        p.drawEllipse(QPointF(fc.x() + fr * dx, eye_y), fr * 0.09, fr * 0.11)
    p.setBrush(QBrush(BLUSH))
    for dx in (-0.6, 0.6):
        p.drawEllipse(QPointF(fc.x() + fr * dx, eye_y + fr * 0.28), fr * 0.14, fr * 0.08)
    p.setPen(_pen(INK, max(1.0, r * 0.05)))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(fc.x() - fr * 0.22, eye_y + fr * 0.1, fr * 0.44, fr * 0.36), 200 * 16, 140 * 16)

    # 캐릭터별 소품
    if character == "범생이":                         # 동그란 안경
        p.setPen(_pen(INK, max(1.0, r * 0.06)))
        for dx in (-0.36, 0.36):
            p.drawEllipse(QPointF(fc.x() + fr * dx, eye_y), fr * 0.24, fr * 0.24)
        p.drawLine(QPointF(fc.x() - fr * 0.12, eye_y), QPointF(fc.x() + fr * 0.12, eye_y))
    elif character == "운동부":                       # 머리띠
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#E5484D")))
        p.drawRoundedRect(QRectF(fc.x() - fr * 1.02, fc.y() - fr * 0.52, fr * 2.04, fr * 0.24), fr * 0.1, fr * 0.1)
    elif character == "감성러":                       # 베레모
        p.setPen(_pen(INK, max(1.0, r * 0.04)))
        p.setBrush(QBrush(QColor("#3D5A9E")))
        p.drawEllipse(QRectF(fc.x() - fr * 1.05, fc.y() - fr * 1.3, fr * 2.0, fr * 0.8))
        p.setBrush(QBrush(QColor("#3D5A9E")))
        p.drawEllipse(QPointF(fc.x() + fr * 0.1, fc.y() - fr * 1.32), fr * 0.1, fr * 0.1)


def _draw_robot(p, c: QPointF, r: float) -> None:
    w = r * 1.15
    head = QRectF(c.x() - w / 2, c.y() - w * 0.35, w, w * 0.8)
    # 안테나
    p.setPen(_pen(INK, max(1.0, r * 0.06)))
    p.drawLine(QPointF(c.x(), head.top()), QPointF(c.x(), head.top() - r * 0.22))
    p.setBrush(QBrush(QColor("#FFC94D")))
    p.drawEllipse(QPointF(c.x(), head.top() - r * 0.28), r * 0.09, r * 0.09)
    # 머리
    p.setBrush(QBrush(QColor("#E9E4F7")))
    p.drawRoundedRect(head, r * 0.18, r * 0.18)
    # 눈
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor("#2BC4B0")))
    for dx in (-0.22, 0.12):
        p.drawRoundedRect(QRectF(c.x() + w * dx, head.top() + w * 0.22, w * 0.12, w * 0.14), 2, 2)
    # 입 (격자)
    p.setBrush(QBrush(INK))
    mouth = QRectF(c.x() - w * 0.22, head.top() + w * 0.5, w * 0.44, w * 0.12)
    p.drawRoundedRect(mouth, 2, 2)
    p.setPen(_pen("#E9E4F7", max(1.0, r * 0.03)))
    for i in range(1, 4):
        x = mouth.left() + mouth.width() * i / 4
        p.drawLine(QPointF(x, mouth.top()), QPointF(x, mouth.bottom()))


class FaceWidget(QWidget):
    """얼굴 하나를 보여 주는 작은 위젯 (상태창 카드·대화창·시상대에 쓴다)"""

    def __init__(self, character: str = "", color=None, npc: bool = False, size: int = 44, parent=None):
        super().__init__(parent)
        self.character, self.color, self.npc = character, color, npc
        self.setFixedSize(size, size)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_face(self, character: str, color=None, npc: bool = False) -> None:
        self.character, self.color, self.npc = character, color, npc
        self.update()

    def paintEvent(self, event) -> None:
        from PyQt5.QtGui import QPainter
        p = QPainter(self)
        draw_face(p, QRectF(1, 1, self.width() - 2, self.height() - 2), self.character, self.color, self.npc)
        p.end()


# ══════════════════════════════════════════════════════════
# 칸 아이콘
# ══════════════════════════════════════════════════════════
def draw_tile_icon(p, rect: QRectF, kind: str, color=None) -> None:
    p.save()
    p.setRenderHint(p.Antialiasing)
    color = QColor(color) if color is not None else INK
    s = min(rect.width(), rect.height())
    c = rect.center()
    if kind == "luck":
        _clover(p, c, s, color)
    elif kind == "badluck":
        _storm(p, c, s, color)
    elif kind == "golden_key":
        _key(p, c, s, color)
    elif kind == "shop":
        _lock(p, c, s, color)
    elif kind == "rest":
        _moon(p, c, s, color)
    elif kind == "start":
        _arrow(p, c, s, color)
    elif kind == "coins":          # 사업 실적·투자 결과
        _coins(p, c, s)
    elif kind == "paper":          # 프리랜서 의뢰
        _paper(p, c, s, color)
    elif kind == "palette":        # 예술가 작품
        _palette(p, c, s, color)
    elif kind == "cap":            # 국가고시
        _cap(p, c, s, color)
    p.restore()


def _coins(p, c, s) -> None:
    """동전 세 개를 쌓은 모양"""
    for i, (dx, dy) in enumerate(((-0.16, 0.12), (0.16, 0.12), (0.0, -0.12))):
        draw_coin(p, QRectF(c.x() + s * dx - s * 0.2, c.y() + s * dy - s * 0.2, s * 0.4, s * 0.4))


def _paper(p, c, s, color) -> None:
    """의뢰서: 접힌 종이 + 글줄 + 도장"""
    w, h = s * 0.5, s * 0.62
    x, y = c.x() - w / 2, c.y() - h / 2
    fold = s * 0.13
    body = QPolygonF([QPointF(x, y), QPointF(x + w - fold, y), QPointF(x + w, y + fold),
                      QPointF(x + w, y + h), QPointF(x, y + h)])
    p.setPen(_pen(INK, s * 0.055))
    p.setBrush(QBrush(QColor("white")))
    p.drawPolygon(body)
    p.setPen(_pen(color, s * 0.045))
    for i in range(3):
        yy = y + h * (0.32 + i * 0.18)
        p.drawLine(QPointF(x + w * 0.18, yy), QPointF(x + w * (0.82 if i < 2 else 0.5), yy))
    p.setPen(_pen(INK, s * 0.03))
    p.setBrush(QBrush(QColor("#FF5D73")))
    p.drawEllipse(QPointF(x + w * 0.78, y + h * 0.8), s * 0.075, s * 0.075)


def _palette(p, c, s, color) -> None:
    """팔레트: 둥근 판 + 물감 네 방울 + 엄지 구멍"""
    board = QPainterPath()
    board.addEllipse(QPointF(c.x(), c.y()), s * 0.36, s * 0.28)
    hole = QPainterPath()
    hole.addEllipse(QPointF(c.x() + s * 0.16, c.y() + s * 0.1), s * 0.06, s * 0.06)
    p.setPen(_pen(INK, s * 0.055))
    p.setBrush(QBrush(QColor("#FFF1D6")))
    p.drawPath(board.subtracted(hole))
    p.setPen(_pen(INK, s * 0.025))
    for (dx, dy), paint in zip(((-0.2, -0.04), (-0.07, -0.15), (0.09, -0.14), (-0.13, 0.12)),
                               ("#FF5D73", "#FFD43B", "#3FA9F5", "#2EC774")):
        p.setBrush(QBrush(QColor(paint)))
        p.drawEllipse(QPointF(c.x() + s * dx, c.y() + s * dy), s * 0.06, s * 0.06)


def _cap(p, c, s, color) -> None:
    """학사모: 마름모 판 + 모자 + 술"""
    p.setPen(_pen(INK, s * 0.045))
    p.setBrush(QBrush(color))
    p.drawRoundedRect(QRectF(c.x() - s * 0.18, c.y() - s * 0.02, s * 0.36, s * 0.22), s * 0.05, s * 0.05)
    top = QPolygonF([QPointF(c.x(), c.y() - s * 0.3), QPointF(c.x() + s * 0.4, c.y() - s * 0.1),
                     QPointF(c.x(), c.y() + s * 0.08), QPointF(c.x() - s * 0.4, c.y() - s * 0.1)])
    p.setBrush(QBrush(color.darker(130) if isinstance(color, QColor) else QColor(color)))
    p.drawPolygon(top)
    p.setPen(_pen("#FFC94D", s * 0.035))
    p.drawLine(QPointF(c.x(), c.y() - s * 0.11), QPointF(c.x() + s * 0.3, c.y() - s * 0.04))
    p.drawLine(QPointF(c.x() + s * 0.3, c.y() - s * 0.04), QPointF(c.x() + s * 0.3, c.y() + s * 0.2))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor("#FFC94D")))
    p.drawEllipse(QPointF(c.x() + s * 0.3, c.y() + s * 0.22), s * 0.04, s * 0.04)


def _fill(p, path, fill, s, width: float = 0.055) -> None:
    """잉크 테두리 + 색 채우기 (스티커 아이콘)"""
    p.setPen(_pen(INK, max(1.2, s * width)))
    p.setBrush(QBrush(QColor(fill)))
    p.drawPath(path)


def _double_line(p, a: QPointF, b: QPointF, color, s, width: float) -> None:
    """굵은 잉크 선 위에 색 선을 겹쳐 '테두리 있는 선'을 만든다"""
    p.setPen(_pen(INK, s * (width + 0.07)))
    p.drawLine(a, b)
    p.setPen(_pen(color, s * width))
    p.drawLine(a, b)


def _union(*paths) -> QPainterPath:
    """겹친 도형을 하나로 합친다 (겹친 곳이 구멍이 되지 않게)"""
    result = QPainterPath()
    result.setFillRule(Qt.WindingFill)
    for path in paths:
        result = result.united(path)
    return result


def _ellipse(center: QPointF, rx: float, ry: float) -> QPainterPath:
    path = QPainterPath()
    path.addEllipse(center, rx, ry)
    return path


def _clover(p, c, s, color) -> None:
    leaf = s * 0.165
    _double_line(p, QPointF(c.x(), c.y() + s * 0.08), QPointF(c.x() + s * 0.13, c.y() + s * 0.36), color, s, 0.07)
    leaves = [_ellipse(QPointF(c.x() + dx * leaf * 0.9, c.y() + dy * leaf * 0.9 - s * 0.06), leaf, leaf)
              for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))]
    _fill(p, _union(*leaves, _ellipse(QPointF(c.x(), c.y() - s * 0.06), leaf * 0.7, leaf * 0.7)), color, s)
    p.setPen(_pen(QColor(255, 255, 255, 150), s * 0.03))         # 잎맥
    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        p.drawLine(QPointF(c.x() + dx * leaf * 0.35, c.y() + dy * leaf * 0.35 - s * 0.06),
                   QPointF(c.x() + dx * leaf * 1.25, c.y() + dy * leaf * 1.25 - s * 0.06))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(255, 255, 255, 110)))
    p.drawEllipse(QPointF(c.x() - leaf * 1.1, c.y() - leaf * 0.5 - s * 0.06), leaf * 0.32, leaf * 0.22)


def _cloud_path(c, s, cy) -> QPainterPath:
    base = QPainterPath()
    base.addRoundedRect(QRectF(c.x() - s * 0.33, cy, s * 0.68, s * 0.16), s * 0.08, s * 0.08)
    return _union(_ellipse(QPointF(c.x() - s * 0.17, cy + s * 0.02), s * 0.16, s * 0.14),
                  _ellipse(QPointF(c.x() + s * 0.04, cy - s * 0.07), s * 0.2, s * 0.19),
                  _ellipse(QPointF(c.x() + s * 0.22, cy + s * 0.04), s * 0.14, s * 0.12), base)


def _storm(p, c, s, color) -> None:
    cy = c.y() - s * 0.12
    bolt = QPainterPath()
    bolt.addPolygon(QPolygonF([QPointF(c.x() + s * 0.04, cy + s * 0.1), QPointF(c.x() - s * 0.12, cy + s * 0.36),
                               QPointF(c.x() - s * 0.01, cy + s * 0.36), QPointF(c.x() - s * 0.08, cy + s * 0.56),
                               QPointF(c.x() + s * 0.15, cy + s * 0.26), QPointF(c.x() + s * 0.04, cy + s * 0.26)]))
    bolt.closeSubpath()
    _fill(p, bolt, "#FFD43B", s, 0.045)
    _fill(p, _cloud_path(c, s, cy), color, s)


def _key(p, c, s, color) -> None:
    gold = QColor(color)
    _double_line(p, QPointF(c.x() - s * 0.08, c.y()), QPointF(c.x() + s * 0.34, c.y()), gold, s, 0.09)
    _double_line(p, QPointF(c.x() + s * 0.2, c.y()), QPointF(c.x() + s * 0.2, c.y() + s * 0.14), gold, s, 0.08)
    _double_line(p, QPointF(c.x() + s * 0.31, c.y()), QPointF(c.x() + s * 0.31, c.y() + s * 0.18), gold, s, 0.08)
    ring = QPainterPath()
    ring.addEllipse(QPointF(c.x() - s * 0.19, c.y()), s * 0.17, s * 0.17)
    hole = QPainterPath()
    hole.addEllipse(QPointF(c.x() - s * 0.19, c.y()), s * 0.07, s * 0.07)
    _fill(p, ring.subtracted(hole), gold, s)


def _lock(p, c, s, color) -> None:
    """상점: 쇼핑백"""
    p.setPen(_pen(INK, s * 0.13))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(c.x() - s * 0.13, c.y() - s * 0.33, s * 0.26, s * 0.3), 0, 180 * 16)
    p.setPen(_pen(QColor(color).lighter(140), s * 0.06))
    p.drawArc(QRectF(c.x() - s * 0.13, c.y() - s * 0.33, s * 0.26, s * 0.3), 0, 180 * 16)
    bag = QPainterPath()
    bag.addRoundedRect(QRectF(c.x() - s * 0.27, c.y() - s * 0.16, s * 0.54, s * 0.48), s * 0.08, s * 0.08)
    _fill(p, bag, color, s)
    p.setPen(_pen(INK, s * 0.05))
    p.drawLine(QPointF(c.x() - s * 0.12, c.y() + s * 0.04), QPointF(c.x() + s * 0.12, c.y() + s * 0.04))


def _moon(p, c, s, color) -> None:
    moon = QPainterPath()
    moon.addEllipse(QPointF(c.x() - s * 0.05, c.y() + s * 0.03), s * 0.26, s * 0.26)
    cut = QPainterPath()
    cut.addEllipse(QPointF(c.x() + s * 0.09, c.y() - s * 0.09), s * 0.22, s * 0.22)
    _fill(p, moon.subtracted(cut), color, s)
    p.setPen(_pen(INK, s * 0.05))
    z = s * 0.09
    x0, y0 = c.x() + s * 0.2, c.y() - s * 0.34
    p.drawPolyline(QPolygonF([QPointF(x0, y0), QPointF(x0 + z, y0), QPointF(x0, y0 + z), QPointF(x0 + z, y0 + z)]))


def _arrow(p, c, s, color) -> None:
    arrow = QPainterPath()
    arrow.addPolygon(QPolygonF([QPointF(c.x() - s * 0.36, c.y()), QPointF(c.x() - s * 0.06, c.y() - s * 0.26),
                                QPointF(c.x() - s * 0.06, c.y() - s * 0.11), QPointF(c.x() + s * 0.33, c.y() - s * 0.11),
                                QPointF(c.x() + s * 0.33, c.y() + s * 0.11), QPointF(c.x() - s * 0.06, c.y() + s * 0.11),
                                QPointF(c.x() - s * 0.06, c.y() + s * 0.26)]))
    arrow.closeSubpath()
    _fill(p, arrow, "#FFD43B", s)


# ══════════════════════════════════════════════════════════
# 작은 아이콘
# ══════════════════════════════════════════════════════════
def draw_coin(p, rect: QRectF) -> None:
    p.save()
    p.setRenderHint(p.Antialiasing)
    s = min(rect.width(), rect.height())
    c = rect.center()
    p.setPen(_pen(INK, max(1.2, s * 0.09)))
    p.setBrush(QBrush(QColor("#FFC62E")))
    p.drawEllipse(c, s * 0.43, s * 0.43)
    p.setPen(_pen("#D98E00", max(1.0, s * 0.07)))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(c, s * 0.23, s * 0.23)
    p.restore()


def draw_heart(p, rect: QRectF, color="#FF4F93") -> None:
    p.save()
    p.setRenderHint(p.Antialiasing)
    s = min(rect.width(), rect.height())
    x, y = rect.center().x(), rect.center().y()
    path = QPainterPath()
    path.moveTo(x, y + s * 0.36)
    path.cubicTo(x - s * 0.58, y - s * 0.02, x - s * 0.3, y - s * 0.46, x, y - s * 0.16)
    path.cubicTo(x + s * 0.3, y - s * 0.46, x + s * 0.58, y - s * 0.02, x, y + s * 0.36)
    p.setPen(_pen(INK, max(1.2, s * 0.09)))
    p.setBrush(QBrush(QColor(color)))
    p.drawPath(path)
    p.restore()


def draw_crown(p, rect: QRectF, color="#FFC94D") -> None:
    p.save()
    p.setRenderHint(p.Antialiasing)
    w, h = rect.width(), rect.height()
    x, y = rect.left(), rect.top()
    crown = QPolygonF([QPointF(x, y + h), QPointF(x, y + h * 0.25), QPointF(x + w * 0.3, y + h * 0.6),
                       QPointF(x + w * 0.5, y), QPointF(x + w * 0.7, y + h * 0.6), QPointF(x + w, y + h * 0.25),
                       QPointF(x + w, y + h)])
    p.setPen(_pen(INK, max(1.0, h * 0.08)))
    p.setBrush(QBrush(QColor(color)))
    p.drawPolygon(crown)
    p.restore()


class IconWidget(QWidget):
    """작은 아이콘 위젯: kind = coin / heart / crown / 칸 종류"""

    def __init__(self, kind: str, size: int = 18, color=None, parent=None):
        super().__init__(parent)
        self.kind, self.color = kind, color
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        from PyQt5.QtGui import QPainter
        p = QPainter(self)
        r = QRectF(0, 0, self.width(), self.height())
        if self.kind == "coin":
            draw_coin(p, r)
        elif self.kind == "heart":
            draw_heart(p, r)
        elif self.kind == "crown":
            draw_crown(p, r.adjusted(1, 3, -1, -2))
        else:
            draw_tile_icon(p, r, self.kind, self.color)
        p.end()


# ══════════════════════════════════════════════════════════
# 스티커 상자와 별 배지
# ══════════════════════════════════════════════════════════
def draw_sticker(p, rect: QRectF, fill, radius: float = 12, outline: float = 3, shadow: float = 4,
                 lip=None) -> None:
    """스티커 상자. shadow = 아래로 밀린 잉크 그림자 두께, lip = 아래쪽 입체 띠 색 (없으면 생략)"""
    p.save()
    p.setRenderHint(p.Antialiasing)
    if shadow:
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(INK))
        p.drawRoundedRect(rect.translated(0, shadow), radius, radius)
    p.setPen(_pen(INK, outline))
    p.setBrush(QBrush(QColor(fill)))
    p.drawRoundedRect(rect, radius, radius)
    if lip is not None:
        clip = QPainterPath()
        clip.addRoundedRect(rect.adjusted(outline / 2, outline / 2, -outline / 2, -outline / 2), radius, radius)
        p.setClipPath(clip)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(lip)))
        p.drawRect(QRectF(rect.left(), rect.bottom() - rect.height() * 0.16, rect.width(), rect.height() * 0.16))
        p.setClipping(False)
        p.setPen(_pen(INK, outline))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(rect, radius, radius)
    p.restore()


def draw_burst(p, center: QPointF, radius: float, fill, points: int = 12, outline: float = 3) -> None:
    """톱니 별 모양 배지"""
    import math
    poly = QPolygonF()
    for i in range(points * 2):
        r = radius if i % 2 == 0 else radius * 0.8
        a = math.pi * i / points - math.pi / 2
        poly.append(QPointF(center.x() + r * math.cos(a), center.y() + r * math.sin(a)))
    p.save()
    p.setRenderHint(p.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(INK))
    p.drawPolygon(poly.translated(0, 4))
    p.setPen(_pen(INK, outline))
    p.setBrush(QBrush(QColor(fill)))
    p.drawPolygon(poly)
    p.restore()
