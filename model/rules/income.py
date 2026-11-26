"""
model/rules/income.py  —  [팀원 담당] 매 턴 수입과 연금 (규칙 문서: 직업 5개, 노년기·연금)
"""


def turn_income(player, steps: int) -> tuple:
    """(돈, 행복) = 칸당 수입 × 이동한 칸 수. 승진 +10%씩, 결혼 행복 +5, 출산 행복 +5·돈 -50.
    사업가는 business.performance()로 따로 계산한다."""
    raise NotImplementedError("TODO(팀원)")


def pension(player, steps: int) -> tuple:
    """노년기 연금: 칸당 수입 × 칸 수 × 연금 비율(50%, 공무원 80%).
    프리랜서·예술가는 예전 칸당 수입(pension_income) 기준, 사업가는 마지막 업종 실적의 50%(유행 보정 없음)"""
    raise NotImplementedError("TODO(팀원)")
