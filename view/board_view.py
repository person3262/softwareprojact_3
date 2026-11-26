"""
view/board_view.py  —  BoardView: 보드판 출력 (FR-02-02) + 말 이동 애니메이션

보드 구조
  - Model의 Board는 28칸짜리 1차원 리스트다. (0번 = 출발)
  - 화면은 8×8 격자의 테두리만 쓴다: 위 8 + 아래 8 + 왼쪽 6 + 오른쪽 6 = 28칸
  - build_tile_coords()가 "칸 번호 → 격자 (행, 열)" 표를 만든다.
  - 가운데 6×6 영역에는 CenterPanel(로고·인생 지도·차례 배너·주사위·속보 띠)을 올린다.
모양
  - 칸은 스티커: 자주 나오는 행운·불행은 옅은 바탕 + 큰 아이콘, 특별한 칸(출발·휴식·상점·황금열쇠)은 진한 바탕 + 이름
  - 말은 한 칸마다 깡충 뛰며 움직인다 (HOP_MS). 지금 차례인 말의 칸은 그 사람 색 테두리로 표시
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QRectF, QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtWidgets import QWidget, QSizePolicy

from common.constants import BOARD_SIZE, TILE_KIND_NAMES, TILE_KIND_HINTS
from common.adapter import TileInfo, read_tile, read_player
from view import style
from view.painter_kit import draw_tile_icon, draw_sticker
from view.piece_view import PieceView
from view.center_view import CenterPanel

GRID = 8              # 8×8 격자
HOP_MS = 170          # 말이 한 칸 깡충 뛰는 데 걸리는 시간(ms) — 7칸이면 약 1.2초
MOVE_STEP_MS = HOP_MS
HOP_HEIGHT = 0.32     # 뛰는 높이 (칸 너비 대비)
SPECIAL_TILES = ("start", "rest", "shop", "golden_key")

# 설계서 8.2 보드 배치 (Model이 오기 전 기본 그림용. 실제 배치는 set_tiles로 받는다)
DEFAULT_LAYOUT = ["start", "luck", "badluck", "luck", "golden_key", "badluck", "luck", "rest",
                  "badluck", "luck", "badluck", "shop", "luck", "badluck", "golden_key", "luck",
                  "badluck", "luck", "badluck", "luck", "badluck", "shop", "luck", "badluck",
                  "luck", "badluck", "luck", "badluck"]


def build_tile_coords(grid: int = GRID, reverse: bool = False) -> list:
    """칸 번호(0~27) → 격자 좌표 (row, col) 목록.

    0번(출발) = 오른쪽 아래 모서리.
    아래 줄을 따라 왼쪽 → 왼쪽 줄을 따라 위 → 위 줄을 따라 오른쪽 → 오른쪽 줄을 따라 아래 (시계방향).
    reverse=True 이면 출발 칸은 그대로 두고 도는 방향만 반대로 바꾼다.
    """
    last = grid - 1
    coords = []
    for col in range(last, -1, -1):      # 아래 줄: 오른쪽 → 왼쪽 (8칸, 0~7번)
        coords.append((last, col))
    for row in range(last - 1, 0, -1):   # 왼쪽 줄: 아래 → 위   (6칸, 8~13번)
        coords.append((row, 0))
    for col in range(0, grid):           # 위 줄: 왼쪽 → 오른쪽 (8칸, 14~21번)
        coords.append((0, col))
    for row in range(1, last):           # 오른쪽 줄: 위 → 아래 (6칸, 22~27번)
        coords.append((row, last))
    if reverse:
        coords = [coords[0]] + coords[:0:-1]
    return coords


def make_path(start: int, steps: int, size: int = BOARD_SIZE) -> list:
    """start에서 steps칸 움직일 때 밟는 칸 번호들. (원형 보드: % size)
    예) make_path(26, 4) → [27, 0, 1, 2]   / 뒤로 가면 steps가 음수
    """
    step = 1 if steps >= 0 else -1
    return [(start + step * i) % size for i in range(1, abs(steps) + 1)]


class BoardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(660, 660)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.coords = build_tile_coords()
        self.tiles = [TileInfo(k, TILE_KIND_NAMES[k]) for k in DEFAULT_LAYOUT]
        self.pieces: dict = {}          # player_id → PieceView
        self.colors: dict = {}          # player_id → QColor
        self.center = CenterPanel(self)

        # 말 이동 애니메이션 상태: 한 칸씩 깡충
        self._hop = QVariantAnimation(self)
        self._hop.setDuration(HOP_MS)
        self._hop.setStartValue(0.0)
        self._hop.setEndValue(1.0)
        self._hop.setEasingCurve(QEasingCurve.InOutSine)
        self._hop.valueChanged.connect(self._on_hop)
        self._hop.finished.connect(self._next_hop)
        self._moving_piece = None
        self._path: list = []
        self._hop_from = 0
        self._hop_t = 0.0
        self._on_done = None

    # ── Controller(→ Window)가 부르는 함수 ─────────────────────
    def set_tiles(self, tiles) -> None:
        """Model Board의 타일 리스트(28개)를 받아 칸 그림을 바꾼다."""
        infos = [read_tile(t) for t in tiles][:BOARD_SIZE]
        while len(infos) < BOARD_SIZE:
            infos.append(TileInfo("luck", "행운"))
        self.tiles = infos
        self.update()

    def set_pieces(self, players) -> None:
        """게임 시작 시 플레이어 수만큼 말을 만든다. 순서대로 1~4번, 색도 순서대로."""
        self.pieces.clear()
        self.colors.clear()
        for order, p in enumerate(players):
            info = read_player(p)
            color = style.player_color(order)
            piece = PieceView(info.id, order + 1, color, info.is_npc, info.character)
            piece.index = info.position
            self.pieces[info.id] = piece
            self.colors[info.id] = color
        self.center.life_map.set_players(players, self.colors)
        self.update()

    def update_pieces(self, players) -> None:
        """애니메이션 없이 말 위치를 Model 값으로 맞춘다. (이동 중인 말은 건드리지 않음)"""
        for p in players:
            info = read_player(p)
            piece = self.pieces.get(info.id)
            if piece is not None and piece is not self._moving_piece:
                piece.index = info.position
        self.center.life_map.set_players(players, self.colors)
        self.update()

    def set_current_player(self, player) -> None:
        info = read_player(player)
        for pid, piece in self.pieces.items():
            piece.is_current = (pid == info.id)
        self.center.life_map.set_current(info.id)
        self.center.banner.set_player(info, self.colors.get(info.id, QColor(style.INK)))
        self.update()

    def move_piece(self, player_id, from_index: int, steps: int, on_done=None) -> None:
        """말을 한 칸씩 깡충 뛰며 움직인다. 다 움직이면 on_done()을 부른다.

        Controller 쪽에서는 이동이 끝난 뒤에 칸 이벤트를 실행하도록 on_done에 넘기면 된다.
        """
        if self.is_moving():                # 이전 이동이 아직 진행 중이면 즉시 끝낸다
            self._finish_move()
        piece = self.pieces.get(player_id)
        path = make_path(from_index, steps)
        if piece is None or not path:
            if on_done:
                on_done()
            return
        piece.index = from_index % BOARD_SIZE
        self._moving_piece, self._path, self._on_done = piece, path, on_done
        self._start_hop()

    def is_moving(self) -> bool:
        return self._moving_piece is not None

    # ── 애니메이션 내부 ──────────────────────────────────────
    def _start_hop(self) -> None:
        self._hop_from = self._moving_piece.index
        self._hop_t = 0.0
        self._hop.stop()
        self._hop.start()

    def _on_hop(self, value) -> None:
        self._hop_t = float(value)
        self.update()

    def _next_hop(self) -> None:
        if self._moving_piece is None:
            return
        self._moving_piece.index = self._path.pop(0)
        self._hop_t = 0.0
        if self._path:
            self._start_hop()
        else:
            self._finish_move()

    def _finish_move(self) -> None:
        self._hop.stop()
        if self._moving_piece is not None and self._path:
            self._moving_piece.index = self._path[-1]
        callback = self._on_done
        self._moving_piece, self._path, self._on_done = None, [], None
        self._hop_t = 0.0
        self.update()
        if callback:
            callback()

    # ── 좌표 계산 ────────────────────────────────────────────
    def _board_rect(self) -> QRectF:
        """창 크기에 맞춰 가운데에 정사각형 보드 영역을 잡는다. (판 테두리·그림자 자리를 남긴다)"""
        side = min(self.width(), self.height()) - 36
        return QRectF((self.width() - side) / 2, (self.height() - side) / 2 - 4, side, side)

    def tile_rect(self, index: int) -> QRectF:
        board = self._board_rect()
        cell = board.width() / GRID
        row, col = self.coords[index % BOARD_SIZE]
        return QRectF(board.left() + col * cell, board.top() + row * cell, cell, cell)

    def resizeEvent(self, event) -> None:
        board = self._board_rect()
        cell = board.width() / GRID
        inner = board.adjusted(cell + 6, cell + 6, -cell - 6, -cell - 6)
        self.center.setGeometry(inner.toRect())
        super().resizeEvent(event)

    # ── 그리기 ───────────────────────────────────────────────
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        board = self._board_rect()
        # 보드 판: 큰 스티커
        draw_sticker(painter, board.adjusted(-12, -12, 12, 12), "#FFFDF7", radius=30, outline=4, shadow=9)

        current = next((pc for pc in self.pieces.values() if pc.is_current), None)
        for i, tile in enumerate(self.tiles):
            ring = current.color if current is not None and current.index == i and not self.is_moving() else None
            self._draw_tile(painter, self.tile_rect(i), i, tile, ring)

        # 말 (칸 위에 그려야 가려지지 않는다, 현재 차례 말은 맨 위)
        for piece in sorted(self.pieces.values(), key=lambda pc: (pc is self._moving_piece, pc.is_current)):
            if piece is self._moving_piece and self._path:
                a = piece.rect_in(self.tile_rect(self._hop_from))
                b = piece.rect_in(self.tile_rect(self._path[0]))
                t = self._hop_t
                rect = QRectF(a.left() + (b.left() - a.left()) * t, a.top() + (b.top() - a.top()) * t,
                              a.width(), a.height())
                lift = 4 * t * (1 - t) * self.tile_rect(0).width() * HOP_HEIGHT     # 포물선
                piece.draw_at(painter, rect, lift)
            else:
                piece.draw(painter, self.tile_rect(piece.index))
        painter.end()

    def _draw_tile(self, painter, rect: QRectF, index: int, tile: TileInfo, ring=None) -> None:
        bg, accent, fg = style.TILE_STYLE.get(tile.kind, style.TILE_STYLE["luck"])
        cell = rect.width()
        box = rect.adjusted(4, 4, -4, -5)
        special = tile.kind in SPECIAL_TILES
        draw_sticker(painter, box, bg, radius=max(8.0, cell * 0.13), outline=2.5, shadow=3,
                     lip=style.darker(bg, 112))
        if ring is not None:                       # 지금 차례인 사람이 서 있는 칸
            pen = QPen(QColor(ring), 4)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(box.adjusted(-3, -3, 3, 3), cell * 0.16, cell * 0.16)

        # 칸 번호 (왼쪽 위, 작게)
        painter.setPen(QColor(fg if special else style.TEXT_QUIET))
        painter.setFont(style.title_font(max(9, int(cell * 0.11))))
        painter.drawText(box.adjusted(6, 3, 0, 0), Qt.AlignLeft | Qt.AlignTop, str(index))

        if not special:                            # 행운·불행: 큰 아이콘만
            icon = QRectF(box.center().x() - cell * 0.3, box.center().y() - cell * 0.28, cell * 0.6, cell * 0.56)
            draw_tile_icon(painter, icon, tile.kind, accent)
            return
        icon = QRectF(box.center().x() - cell * 0.22, box.top() + box.height() * 0.1, cell * 0.44, cell * 0.4)
        draw_tile_icon(painter, icon, tile.kind, "#FFFFFF" if tile.kind in ("rest", "shop") else accent)
        painter.setPen(QColor(fg))
        painter.setFont(style.title_font(max(11, int(cell * 0.18))))
        label = tile.name or TILE_KIND_NAMES.get(tile.kind, "")
        painter.drawText(QRectF(box.left(), box.top() + box.height() * 0.5, box.width(), cell * 0.22),
                         Qt.AlignCenter, label)
        hint = TILE_KIND_HINTS.get(tile.kind)
        if hint:
            painter.setFont(style.body_font(max(8, int(cell * 0.1)), bold=True))
            painter.drawText(QRectF(box.left() + 2, box.top() + box.height() * 0.71, box.width() - 4, cell * 0.16),
                             Qt.AlignCenter, hint)
