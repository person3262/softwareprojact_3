"""
model/tile.py  —  [팀원 담당] 칸 (상세 설계 13장: Tile을 상속한 6가지)

화면(View)은 tile_type 값으로 칸 그림을 고른다. (common/adapter.py의 TILE_FIELDS)
"""


class Tile:
    tile_type = ""
    tile_name = ""

    def on_land(self, game, player) -> dict:
        """말이 이 칸에 멈췄을 때 효과를 처리하고, 화면에 보여 줄 이벤트 dict를 돌려준다 (없으면 None).
        이벤트 dict 모양은 '역할 분담' 문서의 함수 약속 › 이벤트 dict를 본다."""
        raise NotImplementedError("TODO(팀원): 칸마다 다르게 구현")


class Start(Tile):
    tile_type, tile_name = "start", "출발"         # 멈춰도 효과 없음 (단계 상승은 지날 때)


class Luck(Tile):
    tile_type, tile_name = "luck", "행운"


class Badluck(Tile):
    tile_type, tile_name = "badluck", "불행"


class GoldenKey(Tile):
    tile_type, tile_name = "golden_key", "황금열쇠"


class Rest(Tile):
    tile_type, tile_name = "rest", "휴식"


class Shop(Tile):
    tile_type, tile_name = "shop", "상점"


TILE_CLASSES = {cls.tile_type: cls for cls in (Start, Luck, Badluck, GoldenKey, Rest, Shop)}


def make_tile(kind: str) -> Tile:
    """board.json의 "luck" 같은 문자열 → Luck() 객체"""
    raise NotImplementedError("TODO(팀원): TILE_CLASSES에서 찾아 만든다")
