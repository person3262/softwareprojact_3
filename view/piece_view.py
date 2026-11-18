"""
view/piece_view.py  —  PieceView: 보드 위 플레이어 말 하나 (FR-02-03)

PieceView는 위젯이 아니라 "그리는 방법을 아는 객체"다.
BoardView가 화면을 그릴 때(paintEvent) 각 말의 draw()를 불러 준다.
→ 말을 위젯으로 만들면 보드 크기가 바뀔 때마다 위치를 다시 옮겨야 하지만,
  이렇게 하면 BoardView가 칸 위치만 계산해서 넘겨주면 된다.
"""
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QColor, QPen, QBrush, QFont

from view import style


class PieceView:
    RADIUS_RATIO = 0.14   # 칸 너비 대비 말 반지름

    def __init__(self, player_id: int, number: int, color: QColor, is_npc: bool = False):
        self.player_id = player_id
        self.number = number        # 화면에 보이는 번호(1~4) = 상태창 카드 번호
        self.color = color
        self.is_npc = is_npc
        self.index = 0              # 현재 서 있는 칸 번호(0~27)
        self.is_current = False     # 현재 차례면 테두리를 굵게

    @property
    def slot(self) -> int:
        """한 칸에 말이 여러 개 있을 때 겹치지 않도록 2×2 자리 중 고정 자리를 쓴다."""
        return (self.number - 1) % 4

    def draw(self, painter, tile_rect: QRectF) -> None:
        w, h = tile_rect.width(), tile_rect.height()
        r = w * self.RADIUS_RATIO
        # 칸 위쪽은 칸 이름이 있으므로 말은 아래쪽 2×2 자리에 둔다
        cx = tile_rect.left() + w * (0.30 if self.slot % 2 == 0 else 0.70)
        cy = tile_rect.top() + h * (0.58 if self.slot < 2 else 0.82)
        center = QPointF(cx, cy)

        pen = QPen(QColor(style.HIGHLIGHT), 3 if self.is_current else 1)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.color))
        if self.is_npc:   # NPC 말은 네모, 사람 말은 동그라미
            painter.drawRoundedRect(QRectF(cx - r, cy - r, 2 * r, 2 * r), r * 0.3, r * 0.3)
        else:
            painter.drawEllipse(center, r, r)

        # 가운데 번호
        font = QFont(painter.font())
        font.setPixelSize(max(8, int(r * 1.1)))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("white"))
        painter.drawText(QRectF(cx - r, cy - r, 2 * r, 2 * r), Qt.AlignCenter, str(self.number))
