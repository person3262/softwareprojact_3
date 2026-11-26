"""
model/rules/gig.py  —  [팀원 담당] 프리랜서 의뢰 게시판 (규칙 문서: 직업별 고유 장치 › 프리랜서)
"""


def draw_three(gigs: list, rng) -> list:
    """의뢰 카드 3장 (펼친 3장은 고른 것까지 모두 다시 섞어 넣는다)"""
    raise NotImplementedError("TODO(팀원)")


def settle(player, dice: tuple) -> dict:
    """맡은 의뢰 정산: 보수(gig_double이면 2배) + 정산 주사위로 사고(피해 감소 공식)·대박.
    '쉰다'(player.gig == "rest")였으면 행복 +적당히(+50). 화면용 이벤트 dict(kind "gig")를 돌려준다."""
    raise NotImplementedError("TODO(팀원)")
