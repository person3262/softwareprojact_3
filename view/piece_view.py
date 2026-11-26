"""
view/piece_view.py  —  PieceView: 보드 위 플레이어 말 하나 (FR-02-03)

PieceView는 위젯이 아니라 "그리는 방법을 아는 객체"다.
BoardView가 화면을 그릴 때(paintEvent) 각 말의 draw()를 불러 준다.
→ 말을 위젯으로 만들면 보드 크기가 바뀔 때마다 위치를 다시 옮겨야 하지만,
  이렇게 하면 BoardView가 칸 위치만 계산해서 넘겨주면 된다.
말은 캐릭터 얼굴 토큰이다 (범생이 안경, 운동부 머리띠, 감성러 베레모, NPC 로봇).
바닥 그림자가 있어서 깡충 뛸 때(lift) 떠오르는 것처럼 보인다.
"""
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPen, QBrush, QPolygonF

from view import style
from view.painter_kit import draw_face


class PieceView:
    SIZE_RATIO = 0.42   # 칸 너비 대비 얼굴 크기

    def __init__(self, player_id: int, number: int, color: QColor, is_npc: bool = False, character: str = ""):
        self.player_id = player_id
        self.number = number        # 화면에 보이는 번호(1~4) = 상태창 카드 순서
        self.color = color
        self.is_npc = is_npc
        self.character = character
        self.index = 0              # 현재 서 있는 칸 번호(0~27)
        self.is_current = False     # 현재 차례면 크게 그리고 위에 화살표

    @property
    def slot(self) -> int:
        """한 칸에 말이 여러 개 있을 때 겹치지 않도록 2×2 자리 중 고정 자리를 쓴다."""
        return (self.number - 1) % 4

    def rect_in(self, tile_rect: QRectF) -> QRectF:
        w = tile_rect.width()
        size = w * self.SIZE_RATIO * (1.2 if self.is_current else 1.0)
        cx = tile_rect.left() + w * (0.31 if self.slot % 2 == 0 else 0.69)
        cy = tile_rect.top() + tile_rect.height() * (0.33 if self.slot < 2 else 0.66)
        return QRectF(cx - size / 2, cy - size / 2, size, size)

    def draw(self, painter, tile_rect: QRectF) -> None:
        self.draw_at(painter, self.rect_in(tile_rect), 0.0)

    def draw_at(self, painter, rect: QRectF, lift: float = 0.0) -> None:
        """rect = 바닥 자리, lift = 떠오른 높이(px)"""
        painter.save()
        painter.setRenderHint(painter.Antialiasing)
        shrink = 1.0 - min(0.45, lift / max(1.0, rect.width()))        # 높이 뜰수록 그림자가 작아진다
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(35, 38, 74, 90)))
        painter.drawEllipse(QPointF(rect.center().x(), rect.bottom() - rect.height() * 0.04),
                            rect.width() * 0.42 * shrink, rect.height() * 0.13 * shrink)
        face = rect.translated(0, -lift)
        draw_face(painter, face, self.character, self.color, self.is_npc)
        if self.is_current:          # 현재 차례: 얼굴 위 작은 화살표 (그 사람 색)
            c = face.center().x()
            top = face.top() - 3
            painter.setPen(QPen(QColor(style.INK), 2))
            painter.setBrush(QBrush(self.color))
            painter.drawPolygon(QPolygonF([QPointF(c - 7, top - 10), QPointF(c + 7, top - 10), QPointF(c, top)]))
        painter.restore()
