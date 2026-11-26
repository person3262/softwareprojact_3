"""
model/company.py  —  [팀원 담당] 투자할 회사와 투자 건 (규칙 문서: 투자)

화면(InvestDialog)은 id, name, type, ratios_x10을 읽는다. 회사는 data/companies.json의 기본 회사 3곳뿐이다.
"""


class Company:
    def __init__(self, company_id: str, name: str, type_id: str, ratios_x10: list):
        self.id = company_id
        self.name = name
        self.type = type_id                # "stable" / "growth" / "gamble"
        self.ratios_x10 = ratios_x10       # 합 2~3, 4~5, 6~8, 9~10, 11~12의 배율 × 10

    def ratio_x10(self, dice_sum: int) -> int:
        """주사위 합 → 배율 × 10"""
        raise NotImplementedError("TODO(팀원)")


class Investment:
    def __init__(self, company: Company, amount: int, turns_left: int = 5):
        self.company = company
        self.amount = amount               # 투자 금액 (만원)
        self.turns_left = turns_left       # 자기 턴이 지날 때마다 1씩 줄고, 0이 되면 정산
