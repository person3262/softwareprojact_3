"""
model/rules/shop.py  —  [팀원 담당] 상점 (규칙 문서: 상점)
"""


def items_for(player, shop: list, scale: dict) -> list:
    """그 단계 가격·효과를 숫자로 바꾼 상품 목록. 인강 패스는 의대생에게만.
    화면(ShopDialog)은 name, price, stats, description을 읽는다."""
    raise NotImplementedError("TODO(팀원)")


def buy(player, item: dict) -> dict:
    """돈을 빼고 효과 적용 (보험 → player.insurance, 인강 패스 → player.lecture_pass). 화면용 이벤트 dict"""
    raise NotImplementedError("TODO(팀원)")
