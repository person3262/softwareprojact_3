"""
model/rules/events.py  —  [팀원 담당] 행운·불행 이벤트 (규칙 문서: 이벤트)
"""


def pick_event(events: list, player, kind: str, rng):
    """그 사람의 단계에 맞는 이벤트를 하나 뽑는다.
    유아기·청년기·노년기: 그 단계 표 / 성년기·중년기: 내 직업 3개 + 공통 3개 /
    의대생: 청년기 이벤트 + 수험생 이벤트 (청년기 수치)"""
    raise NotImplementedError("TODO(팀원)")


def reduce_damage(base: int, stat_value: int, athlete: bool = False, insurance: bool = False) -> int:
    """불행 피해 감소. base는 음수(피해).
    실제 피해 = 기본 피해 × (200 − 능력치) ÷ 200 → 운동부 ×80÷100 → 보험 ×50÷100 (모두 정수 나눗셈)
    예) reduce_damage(-50, 34) → -41"""
    raise NotImplementedError("TODO(팀원)")


def apply_event(player, event: dict, scale: dict, multiplier: int = 1) -> dict:
    """이벤트를 적용하고 화면용 dict를 돌려준다.
    불행이면 base_money/base_happiness(줄기 전), reduce_stat, reduce_value, reduce_percent도 넣는다
    → 화면에 '행복 -50 → -41, 체력 34 덕분에 18% 덜 아팠어요'가 나온다."""
    raise NotImplementedError("TODO(팀원)")
