"""
model/rules/business.py  —  사업가 업종과 유행 (규칙 문서: 직업별 고유 장치 › 사업가: 업종과 유행)

★ 예시 구현: 팀장이 규칙을 정하면서 만들어 둔 코드다 (금액은 만원).
  팀원이 읽고 이해한 뒤 그대로 써도 되고, 고쳐 써도 되고, 지우고 새로 짜도 된다.
  업종 표는 data/business.json에서 읽은 dict를 넘겨받는다.

규칙 요약
  - 매 턴 실적 = 그 턴 주사위 합(+ 유행 보정)으로 정한 단계(적자·보통·호황·대박)의 금액
  - 유행 업종은 실적 판정 합 +1 (NFT 갤러리는 +3), NFT 갤러리는 NFT가 유행이 아니면 -1
  - 유행: 시작할 때와 4라운드마다 4가지(세 업종 + 유행 없음) 중 무작위
  - 업종 바꾸기: 출발 칸을 지날 때만, 비용 1,000만원
"""
import random

from common.constants import BUSINESS_TIERS

SWITCH_COST = 1000           # 업종 바꾸기 비용 (만원)
TREND_ROUNDS = 4


def tier_of(total: int) -> int:
    """보정한 주사위 합 → 단계 번호 0~3. 2보다 작으면 적자, 12보다 크면 대박으로 본다."""
    if total <= 4:
        return 0
    if total <= 8:
        return 1
    if total <= 11:
        return 2
    return 3


def trend_modifier(business: dict, trend_id) -> int:
    """유행 보정값: 유행 업종이면 +trend_bonus, 아니면 off_trend (NFT만 -1)"""
    return business["trend_bonus"] if trend_id == business["id"] else business["off_trend"]


def performance(business: dict, dice_sum: int, trend_id=None, use_trend: bool = True) -> dict:
    """그 턴 실적을 화면용 이벤트 dict로 돌려준다. use_trend=False면 유행 보정 없음 (노년기 연금)."""
    bonus = trend_modifier(business, trend_id) if use_trend else 0
    total = dice_sum + bonus
    tier = tier_of(total)
    money, happiness = business["table"][tier]
    sign = f" {'+' if bonus > 0 else '-'} {abs(bonus)}" if bonus else ""
    return {"kind": "business", "name": f"{business['name']} 실적: {BUSINESS_TIERS[tier]}",
            "description": f"주사위 합 {dice_sum}{sign} = {total}",
            "money": money, "happiness": happiness, "tier": tier, "total": total}


class Trend:
    """지금 유행과 남은 라운드. Controller가 라운드가 끝날 때마다 end_round()를 부른다."""

    def __init__(self, business_data: dict, rng: random.Random = None, rounds: int = TREND_ROUNDS):
        """business_data: data/business.json 전체 (businesses, headlines, nft_names)"""
        self.data = business_data
        self.rng = rng or random.Random()
        self.rounds = rounds
        self.current = None
        self.rounds_left = 0
        self.nft_name = business_data["nft_names"][0]

    def start(self) -> str:
        """첫 유행을 정하고 속보 문구를 돌려준다."""
        return self._pick()

    def end_round(self) -> list:
        """라운드가 끝났다. 유행이 바뀌면 [끝 문구, 새 유행 문구], 아니면 []"""
        self.rounds_left -= 1
        if self.rounds_left > 0:
            return []
        ending = self.headline(self.current, start=False)
        return ([ending] if ending else []) + [self._pick()]

    def headline(self, trend_id, start: bool = True) -> str:
        text = self.data["headlines"][trend_id or "none"][0 if start else 1]
        return text.format(nft=self.nft_name)

    def label(self) -> str:
        """화면 표시줄 문구. 예) '지금 유행: NFT 갤러리 (2라운드 남음)' → window.set_trend(...)"""
        name = next((b["name"] for b in self.data["businesses"] if b["id"] == self.current), None)
        if name is None:
            return f"지금은 유행이 없어요 ({self.rounds_left}라운드 남음)"
        return f"지금 유행: {name} ({self.rounds_left}라운드 남음)"

    def _pick(self) -> str:
        choices = [b["id"] for b in self.data["businesses"]] + [None]
        self.current = self.rng.choice(choices)
        self.rounds_left = self.rounds
        if self.current == "nft":
            self.nft_name = self.rng.choice(self.data["nft_names"])
        return self.headline(self.current, start=True)
