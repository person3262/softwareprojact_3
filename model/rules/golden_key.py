"""
model/rules/golden_key.py  —  [팀원 담당] 황금열쇠 (규칙 문서: 이벤트 › 황금열쇠)
"""
MAX_KEEP = 3


def build_deck(cards: list, rng) -> list:
    """golden_keys.json의 count만큼 넣고 섞은 덱 (10장). 다 쓰면 다시 만든다."""
    raise NotImplementedError("TODO(팀원)")


def draw(player, deck: list, scale: dict, rng) -> dict:
    """한 장 뽑기. 복권·꽝은 즉시, 보관 카드는 player.items에 (최대 3장). 화면용 이벤트 dict(kind "golden_key")"""
    raise NotImplementedError("TODO(팀원)")


def take(player, card_id: str) -> bool:
    """보관 카드를 꺼내 쓴다 (있으면 True). 행운 보상 2배·다음 투자 상승은 자동, 불운→행운은 물어보고"""
    raise NotImplementedError("TODO(팀원)")
