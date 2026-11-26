"""
model/rules/invest.py  —  [팀원 담당] 투자 (규칙 문서: 투자)
"""
INVEST_EVERY = 5        # 성년기부터 자기 턴 5번마다 기회
INVEST_WAIT = 5         # 5턴 뒤 정산


def is_invest_turn(player) -> bool:
    raise NotImplementedError("TODO(팀원)")


def invest(player, company, amount: int) -> dict:
    """돈을 빼고 Investment를 player.investments에 넣는다. 화면용 이벤트 dict(kind "invest")"""
    raise NotImplementedError("TODO(팀원)")


def settle(player, investment, dice: tuple) -> dict:
    """금액 × 배율 ÷ 10 (정수). 다음 투자 상승 카드가 있으면 배율 +5(= +0.5).
    수익이면 행복 +조금, 손실이면 -조금"""
    raise NotImplementedError("TODO(팀원)")
