"""
tests/test_model.py  —  [팀원 담당] Model 규칙 테스트

숫자는 모두 게임 규칙 문서의 예시에서 가져왔다. 함수를 구현하면 해당 클래스의 @skip 줄을 지운다.
사업가(rules/business.py)는 예시 구현이 있어서 지금도 돌아간다.
"""
import json
import os
import unittest

from tests import helpers  # noqa: F401  (경로 준비)
from model.rules import business

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


class TestBusinessExample(unittest.TestCase):
    """예시 구현 — 규칙 문서 '사업가: 업종과 유행'의 예시와 같은지"""

    def setUp(self):
        self.data = load("business.json")
        self.by_id = {b["id"]: b for b in self.data["businesses"]}

    def test_story_from_rules_doc(self):
        """하늘: NFT 유행일 때 합 9 + 3 = 12 대박(+3,500만원), 스마트스토어 유행일 때 합 5 - 1 = 4 적자(-800만원)"""
        nft = self.by_id["nft"]
        self.assertEqual(business.performance(nft, 9, "nft")["money"], 3500)
        self.assertEqual(business.performance(nft, 5, "store")["money"], -800)

    def test_no_trend_probabilities(self):
        """유행 보정이 없을 때 적자 6 · 보통 20 · 호황 9 · 대박 1 (36가지 중)"""
        tiers = [business.tier_of(a + b) for a in range(1, 7) for b in range(1, 7)]
        self.assertEqual([tiers.count(t) for t in range(4)], [6, 20, 9, 1])

    def test_trend_changes_every_4_rounds(self):
        import random
        trend = business.Trend(self.data, random.Random(1))
        trend.start()
        self.assertEqual([len(trend.end_round()) > 0 for _ in range(4)], [False, False, False, True])
        self.assertIn("라운드 남음", trend.label())


@unittest.skip("TODO(팀원): model/rules 구현 후 이 줄을 지운다")
class TestRules(unittest.TestCase):
    def test_scale(self):
        from model.rules.scale import value
        scale = load("scale.json")["scale"]
        self.assertEqual(value(scale, "성년기", "money", "+적당히"), 500)
        self.assertEqual(value(scale, "유아기", "지력", "-조금"), -3)

    def test_damage_reduction(self):
        from model.rules.events import reduce_damage
        self.assertEqual(reduce_damage(-50, 34), -41)            # 화면 예시 '행복 -50 → -41'
        self.assertEqual(reduce_damage(-700, 40), -560)          # 진상 클라이언트 예시
        self.assertEqual(reduce_damage(-100, 0), -100)
        self.assertEqual(reduce_damage(-100, 100), -50)

    def test_exam_time_limit(self):
        from model.rules.exam import time_limit
        self.assertEqual(time_limit(60), 16)
        self.assertEqual(time_limit(80), 18)
        self.assertEqual(time_limit(60, lecture_pass=True), 26)

    def test_artwork_grade(self):
        from model.rules.artwork import artwork_score, grade_of
        grades = load("art.json")["art"]["grades"]
        self.assertEqual(artwork_score(5, 4, 60), 12)
        self.assertEqual(grade_of(6, grades)["name"], "망작")
        self.assertEqual(grade_of(7, grades)["name"], "습작")

    def test_ranking_tie_breaks_by_money(self):
        from model.rules.score import ranking
        # TODO(팀원): 총점이 같으면 돈이 많은 사람이 앞


if __name__ == "__main__":
    unittest.main()
