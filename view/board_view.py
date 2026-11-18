"""
view/board_view.py  —  BoardView: 보드판 출력 (FR-02-02) + 말 이동 애니메이션

보드 구조
  - Model의 Board는 28칸짜리 1차원 리스트다. (0번 = 출발)
  - 화면은 8×8 격자의 테두리만 쓴다: 위 8 + 아래 8 + 왼쪽 6 + 오른쪽 6 = 28칸
  - build_tile_coords()가 "칸 번호 → 격자 (행, 열)" 표를 만든다.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt5.QtWidgets import QWidget, QSizePolicy

from common.adapter import BOARD_SIZE, TileInfo, read_tile, read_player
from view import style
from view.piece_view import PieceView

GRID = 8              # 8×8 격자
MOVE_STEP_MS = 120    # 말이 한 칸 움직이는 데 걸리는 시간(ms) — NFR-02 지연 최소화


def build_tile_coords(grid: int = GRID, reverse: bool = False) -> list:
    """칸 번호(0~27) → 격자 좌표 (row, col) 목록.

    0번(출발) = 오른쪽 아래 모서리.
    아래 줄을 따라 왼쪽 → 왼쪽 줄을 따라 위 → 위 줄을 따라 오른쪽 → 오른쪽 줄을 따라 아래.
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
        self.setMinimumSize(520, 520)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.coords = build_tile_coords()
        self.tiles = [TileInfo("start", "출발")] + [TileInfo("normal") for _ in range(BOARD_SIZE - 1)]
        self.pieces: dict = {}          # player_id → PieceView
        self.title = "인생마불"
        self.center_text = ""           # 보드 가운데 작은 안내 문구

        # 말 이동 애니메이션 상태
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._moving_piece = None
        self._path: list = []
        self._on_done = None

    # ── Controller(→ Window)가 부르는 함수 ─────────────────────
    def set_tiles(self, tiles) -> None:
        """Model Board의 타일 리스트(28개)를 받아 칸 그림을 바꾼다."""
        infos = [read_tile(t) for t in tiles][:BOARD_SIZE]
        while len(infos) < BOARD_SIZE:
            infos.append(TileInfo("normal"))
        self.tiles = infos
        self.update()

    def set_pieces(self, players) -> None:
        """게임 시작 시 플레이어 수만큼 말을 만든다. 순서대로 1~4번, 색도 순서대로."""
        self.pieces.clear()
        for order, p in enumerate(players):
            info = read_player(p)
            piece = PieceView(info.id, order + 1, style.player_color(order), info.is_npc)
            piece.index = info.position
            self.pieces[info.id] = piece
        self.update()

    def update_pieces(self, players) -> None:
        """애니메이션 없이 말 위치를 Model 값으로 맞춘다. (이동 중인 말은 건드리지 않음)"""
        for p in players:
            info = read_player(p)
            piece = self.pieces.get(info.id)
            if piece is not None and piece is not self._moving_piece:
                piece.index = info.position
        self.update()

    def set_current_player(self, player_id) -> None:
        for pid, piece in self.pieces.items():
            piece.is_current = (pid == player_id)
        self.update()

    def set_center_text(self, text: str) -> None:
        self.center_text = text
        self.update()

    def move_piece(self, player_id, from_index: int, steps: int, on_done=None) -> None:
        """말을 한 칸씩 움직이는 애니메이션. 다 움직이면 on_done()을 부른다.

        Controller 쪽에서는 이동이 끝난 뒤에 칸 이벤트를 실행하도록 on_done에 넘기면 된다.
        """
        if self._timer.isActive():          # 이전 이동이 아직 진행 중이면 즉시 끝낸다
            self._finish_move()
        piece = self.pieces.get(player_id)
        path = make_path(from_index, steps)
        if piece is None or not path:
            if on_done:
                on_done()
            return
        piece.index = from_index % BOARD_SIZE
        self._moving_piece, self._path, self._on_done = piece, path, on_done
        self._timer.start(MOVE_STEP_MS)

    def is_moving(self) -> bool:
        return self._timer.isActive()

    # ── 애니메이션 내부 ──────────────────────────────────────
    def _step(self) -> None:
        if not self._path:
            self._finish_move()
            return
        self._moving_piece.index = self._path.pop(0)
        self.update()
        if not self._path:
            self._finish_move()

    def _finish_move(self) -> None:
        self._timer.stop()
        if self._moving_piece is not None and self._path:
            self._moving_piece.index = self._path[-1]
        callback = self._on_done
        self._moving_piece, self._path, self._on_done = None, [], None
        self.update()
        if callback:
            callback()

    # ── 좌표 계산 ────────────────────────────────────────────
    def _board_rect(self) -> QRectF:
        """창 크기에 맞춰 가운데에 정사각형 보드 영역을 잡는다."""
        side = min(self.width(), self.height()) - 16
        return QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)

    def tile_rect(self, index: int) -> QRectF:
        board = self._board_rect()
        cell = board.width() / GRID
        row, col = self.coords[index % BOARD_SIZE]
        return QRectF(board.left() + col * cell, board.top() + row * cell, cell, cell)

    # ── 그리기 ───────────────────────────────────────────────
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        board = self._board_rect()
        cell = board.width() / GRID
        inner = board.adjusted(cell, cell, -cell, -cell)

        # 1) 가운데 바탕 + 제목
        painter.fillRect(inner, QColor(style.BOARD_BG))
        title_font = QFont(self.font())
        title_font.setPixelSize(int(cell * 0.6))
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor(style.TEXT))
        painter.drawText(inner.adjusted(0, 0, 0, -cell * 0.8), Qt.AlignCenter, self.title)
        if self.center_text:
            sub_font = QFont(self.font())
            sub_font.setPixelSize(max(10, int(cell * 0.22)))
            painter.setFont(sub_font)
            painter.setPen(QColor(style.TEXT_QUIET))
            painter.drawText(inner.adjusted(0, cell * 0.9, 0, 0), Qt.AlignCenter, self.center_text)

        # 2) 칸 28개
        for i, tile in enumerate(self.tiles):
            self._draw_tile(painter, self.tile_rect(i), i, tile)

        # 3) 말 (칸 위에 그려야 가려지지 않는다)
        for piece in self.pieces.values():
            piece.draw(painter, self.tile_rect(piece.index))
        painter.end()

    def _draw_tile(self, painter, rect: QRectF, index: int, tile: TileInfo) -> None:
        painter.setPen(QPen(QColor(style.LINE), 1))
        painter.setBrush(QBrush(QColor(style.TILE_COLORS.get(tile.kind, "#FFFFFF"))))
        painter.drawRect(rect)

        cell = rect.width()
        # 칸 번호(작게, 왼쪽 위) — 디버깅할 때 편하다
        small = QFont(self.font())
        small.setPixelSize(max(8, int(cell * 0.13)))
        painter.setFont(small)
        painter.setPen(QColor(style.TEXT_QUIET))
        painter.drawText(rect.adjusted(3, 1, 0, 0), Qt.AlignLeft | Qt.AlignTop, str(index))

        # 칸 이름(이름이 없으면 종류 이름: 행운/불행/상점…)
        label = tile.name or style.TILE_KIND_NAMES.get(tile.kind, "")
        if tile.kind == "start":
            label = f"← {label or '출발'}"   # 말은 아래 줄을 따라 왼쪽으로 출발한다
        name_font = QFont(self.font())
        name_font.setPixelSize(max(9, int(cell * 0.17)))
        name_font.setBold(tile.kind == "start")
        painter.setFont(name_font)
        painter.setPen(QColor(style.TEXT))
        painter.drawText(rect.adjusted(2, cell * 0.14, -2, -cell * 0.55),
                         Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextWordWrap, label)
