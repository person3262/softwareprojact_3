"""
model/rules/score.py  —  [팀원 담당] 총점과 순위 (규칙 문서: 노년기, 연금, 게임 끝과 결과)
"""
from common.constants import total_score   # 총점 = 돈 + 행복 × 10 (팀장·팀원 공용)


def ranking(players: list) -> list:
    """총점 높은 순, 같으면 돈 많은 순.
    [{"name", "job", "money", "happiness", "score", "character", "is_npc"}, ...] → window.show_result(...)"""
    raise NotImplementedError("TODO(팀원)")
