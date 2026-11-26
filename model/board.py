"""
model/board.py  —  [팀원 담당] 28칸 보드 (규칙 문서: 보드와 칸 종류)
"""
from common.constants import BOARD_SIZE


class Board:
    def __init__(self, kinds: list):
        """kinds: board.json의 칸 종류 28개 (0번 = 출발)"""
        self.tiles = []        # TODO(팀원): make_tile로 Tile 객체 28개를 만든다

    def tile_at(self, index: int):
        raise NotImplementedError("TODO(팀원)")

    def move(self, position: int, steps: int) -> tuple:
        """(새 위치, 출발 칸을 지났는지)를 돌려준다.
        출발 칸에 정확히 멈춰도 '지났다'로 본다. 새 위치는 (position + steps) % BOARD_SIZE"""
        raise NotImplementedError("TODO(팀원): 규칙 문서 '보드와 칸 종류'")
