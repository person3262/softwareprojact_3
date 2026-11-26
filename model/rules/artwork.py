"""
model/rules/artwork.py  —  [팀원 담당] 예술가 작품과 회고전 (규칙 문서: 직업별 고유 장치 › 예술가)
"""


def artwork_score(d1: int, d2: int, sense: int) -> int:
    """작품 점수 = 주사위 합 + 센스 ÷ 20. 예) 5 + 4 + 60 ÷ 20 = 12"""
    raise NotImplementedError("TODO(팀원)")


def grade_of(score: int, grades: list) -> dict:
    """6 이하 망작, 7~9 습작, 10~12 수작, 13 이상 명작 (art.json의 min 값)"""
    raise NotImplementedError("TODO(팀원)")


def make_artwork(player, art: dict, used_titles: set, rng) -> dict:
    """{"id", "title", "grade", "price"} — 제목은 한 판에서 다시 쓰지 않는다 (다 쓰면 다시 섞기)"""
    raise NotImplementedError("TODO(팀원)")


def retrospective(player) -> dict:
    """노년기 회고전: 작업실 작품을 모두 판매가의 2배에 판다. 화면용 이벤트 dict(kind "artwork")"""
    raise NotImplementedError("TODO(팀원)")
