"""
model/rules/scale.py  —  [팀원 담당] 크기 단어('조금·적당히·많이') → 그 단계 숫자 (규칙 문서: 인생 단계)
"""
SIZES = {"조금": 0, "적당히": 1, "많이": 2}


def value(scale: dict, stage: str, kind: str, word: str) -> int:
    """value(scale, "성년기", "money", "+적당히") → 500, value(scale, "유아기", "지력", "-조금") → -3
    kind: "money" / "happiness" / 능력치 이름(→ scale의 "stat" 줄)"""
    raise NotImplementedError("TODO(팀원)")
