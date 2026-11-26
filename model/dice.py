"""
model/dice.py  —  [팀원 담당] 주사위 2개
"""
import random


class Dice:
    def __init__(self, rng: random.Random = None):
        self.rng = rng or random.Random()     # 테스트에서는 random.Random(1)처럼 고정해서 넣는다

    def roll(self) -> tuple:
        """(d1, d2) — 각각 1~6"""
        raise NotImplementedError("TODO(팀원)")
