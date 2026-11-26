"""
model/rules/exam.py  —  [팀원 담당] 의사 국가고시 (규칙 문서: 직업별 고유 장치 › 의사: 국가고시)
"""


def time_limit(intellect: int, lecture_pass: bool = False) -> int:
    """제한 시간(초) = 10 + 지력 ÷ 10 (+10초 인강 패스). 지력 60 → 16초"""
    raise NotImplementedError("TODO(팀원)")


def next_question(questions: list, level: int, used: set, rng) -> dict:
    """그 단계에서 아직 안 나온 문제 하나. 다 썼으면 그 단계 문제를 다시 섞는다."""
    raise NotImplementedError("TODO(팀원)")


def grade(player, question: dict, answer) -> dict:
    """맞히면 합격(의사 확정, 1단계 행복 +많이 / 2~5단계 +조금), 틀리거나 None(시간 초과)이면 불합격.
    반환 이벤트 dict에 "passed": True/False"""
    raise NotImplementedError("TODO(팀원)")


def retry(player) -> bool:
    """재수: exam_level + 1. 5단계에서 떨어졌으면 False (불합격 확정 → 다른 직업)"""
    raise NotImplementedError("TODO(팀원)")
