"""NPC 판단 (npc/npc.py) — 게임 규칙 문서 'NPC 규칙'대로 고르는지"""
import random
import unittest

from tests.helpers import player
from npc import NPC
from npc.npc import gig_value, expected_retakes_x1000, exam_pass_chance_x10, job_value
from dev_stub import fake_data as D


def npc(seed=1):
    return NPC(random.Random(seed))


class TestNumbers(unittest.TestCase):
    def test_gig_values_match_rules_table(self):
        """규칙 문서: 능력치 45 기준 진상 1,008 · 해외 974 · 대기업 892 · 열정페이 450 (반올림 차이 ±1)"""
        stats = {"지력": 45, "체력": 45, "센스": 45}
        values = {g["id"]: gig_value(g, stats) for g in D.GIGS}
        for gid, expected in (("jerk", 1008), ("abroad", 974), ("corp", 892), ("startup", 450), ("public", 774)):
            self.assertAlmostEqual(values[gid], expected, delta=1)

    def test_exam_chance_and_retakes(self):
        self.assertEqual(exam_pass_chance_x10(1, 60), 300)       # 30.0%
        self.assertEqual(exam_pass_chance_x10(5, 100), 950)      # 최대 95%
        self.assertEqual(exam_pass_chance_x10(1, 0), 50)         # 최소 5%
        self.assertAlmostEqual(expected_retakes_x1000(60) / 1000, 1.28, delta=0.01)

    def test_doctor_pays_for_retakes(self):
        doctor = D.JOBS[0]
        self.assertLess(job_value(doctor, 50), job_value(doctor, 90))


class TestChoices(unittest.TestCase):
    def test_job_only_eligible_and_best(self):
        p = player(player_stats={"지력": 50, "체력": 30, "센스": 30})
        self.assertEqual(npc().ask_job(p, D.JOBS), "civil")              # 지력 45 이상 → 공무원 > 프리랜서
        p = player(player_stats={"지력": 10, "체력": 10, "센스": 10})
        self.assertEqual(npc().ask_job(p, D.JOBS), "freelancer")         # 조건 없는 직업은 항상 가능
        self.assertNotEqual(npc().ask_job(player(player_stats={"지력": 99, "체력": 0, "센스": 0}), D.JOBS,
                                          exclude=("doctor",)), "doctor")

    def test_job_change_keeps_when_not_better(self):
        p = player(player_job={"id": "civil", "name": "공무원"}, player_stats={"지력": 50, "체력": 30, "센스": 30})
        self.assertIsNone(npc().ask_job(p, D.JOBS, allow_keep=True))

    def test_invest_by_rank(self):
        companies = D.COMPANIES
        me = player(player_id=0, player_money=2500)
        rich = player(player_id=1, player_money=90000)
        poor = player(player_id=2, player_money=0, player_happiness=0)
        choice = npc().ask_invest(me, companies, [me, rich, poor])        # 중간 → 성장형
        self.assertEqual(choice, {"company_id": "future_bio", "amount": 1000})   # (2500 - 500) × 50%
        self.assertEqual(npc().ask_invest(rich, companies, [me, rich, poor])["company_id"], "tuntun")
        self.assertEqual(npc().ask_invest(player(player_id=2, player_money=1500, player_happiness=-500),
                                          companies, [me, rich, poor])["company_id"], "hanbang")
        self.assertIsNone(npc().ask_invest(player(player_money=400), companies, [me]))   # 비상금 500 미만

    def test_business(self):
        self.assertEqual(npc().ask_business(player(), D.BUSINESSES, "nft"), "nft")
        self.assertEqual(npc().ask_business(player(), D.BUSINESSES, None), "youtube")
        p = player(player_money=2500)
        self.assertEqual(npc().ask_switch_business(p, D.BUSINESSES, "youtube", "nft", 2), "nft")
        self.assertIsNone(npc().ask_switch_business(p, D.BUSINESSES, "youtube", "nft", 1))      # 끝물
        self.assertIsNone(npc().ask_switch_business(player(player_money=1500), D.BUSINESSES, "youtube", "nft", 3))

    def test_gig_and_rest(self):
        self.assertEqual(npc().ask_gig(player(), D.GIGS), "jerk")
        cheap = [g for g in D.GIGS if g["id"] in ("startup", "free")]
        self.assertIsNone(npc().ask_gig(player(), cheap))                  # 500점(쉬기)보다 작으면 쉰다

    def test_artwork(self):
        studio = [{"id": "a", "title": "A", "price": 300}, {"id": "b", "title": "B", "price": 100}]
        self.assertIsNone(npc().ask_artwork(player(), {"id": "c", "price": 30}, studio[:1]))
        self.assertEqual(npc().ask_artwork(player(), {"id": "c", "price": 800}, studio), "b")

    def test_shop(self):
        items = [{"id": "academy", "name": "학원", "price": 30, "stats": {"지력": 5}},
                 {"id": "gym", "name": "헬스장", "price": 30, "stats": {"체력": 5}},
                 {"id": "insurance", "name": "보험", "price": 10}]
        kid = player(player_age=0, player_money=100, player_stats={"지력": 40, "체력": 20, "센스": 45})
        self.assertIsNotNone(npc().ask_shop(kid, items, D.JOBS))
        adult = player(player_age=2, player_money=2000, job_state="employed")
        self.assertEqual(npc().ask_shop(adult, items), 2)                   # 보험
        self.assertIsNone(npc().ask_shop(player(player_age=2, player_money=505, job_state="employed"), items))

    def test_exam_and_cards(self):
        q = {"id": "q", "level": 5, "question": "?", "choices": ["a", "b", "c", "d"], "answer": 3}
        answers = [npc(seed).ask_exam_answer(player(player_stats={"지력": 100, "체력": 0, "센스": 0}), q) for seed in range(200)]
        self.assertGreater(answers.count(3), 170)                          # 95% 정도는 정답
        self.assertTrue(all(1 <= a <= 4 for a in answers))
        self.assertTrue(npc().ask_retry_exam(player(), 3))
        card = {"id": "bad_to_good", "name": "불운→행운 변경권"}
        self.assertTrue(npc().ask_use_card(player(), card, {"name": "의료 분쟁", "size": "많이"}))
        self.assertFalse(npc().ask_use_card(player(), card, {"name": "비", "size": "조금"}))

    def test_think_delay(self):
        self.assertTrue(all(800 <= npc(s).think_delay_ms() <= 1200 for s in range(20)))


if __name__ == "__main__":
    unittest.main()
