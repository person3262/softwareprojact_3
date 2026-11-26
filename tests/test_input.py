"""Input (user_input/input_handler.py) — 창은 가짜 함수로 바꿔 끼우고, 감지·변환·잠금만 검사한다"""
import unittest

from tests.helpers import app, player
from view import Window
from user_input import Input
from dev_stub import fake_data as D


class InputTestCase(unittest.TestCase):
    def setUp(self):
        app()
        self.window = Window()
        self.input = Input(self.window)
        self.popup = self.window.popup_view
        self.events = []
        self.input.roll_requested.connect(lambda: self.events.append("roll"))
        self.input.end_turn_requested.connect(lambda: self.events.append("end"))
        self.input.invest_requested.connect(lambda: self.events.append("invest"))

    def tearDown(self):
        self.window.close()


class TestLock(InputTestCase):
    def test_locked_until_unlock(self):
        button = self.window.dice_view.roll_button
        self.assertFalse(button.isEnabled())
        self.input._on_roll_clicked()                 # 잠긴 동안 누름 → 무시 (NPC 차례·이동 중)
        self.assertEqual(self.events, [])
        self.input.unlock()
        button.click()
        button.click()                                # 두 번 눌러도 한 번만 굴린다
        self.assertEqual(self.events, ["roll"])
        self.assertTrue(self.input.is_locked())

    def test_end_turn_mode(self):
        self.input.unlock_actions(can_invest=True)
        self.assertEqual(self.window.dice_view.roll_button.text(), "턴 마치기")
        self.assertTrue(self.window.dice_view.invest_button.isEnabled())
        self.window.dice_view.invest_button.click()
        self.window.dice_view.roll_button.click()
        self.assertEqual(self.events, ["invest", "end"])
        self.assertEqual(self.window.dice_view.roll_button.text(), "주사위 굴리기!")


class TestConvert(InputTestCase):
    def test_setup_with_npc_character(self):
        self.popup.ask_setup = lambda validator: [{"name": " 정민 ", "is_npc": False}, {"name": "로봇", "is_npc": True}]
        self.popup.ask_character = lambda name, chars, taken: "scholar"
        rows = self.input.run_setup(D.CHARACTERS, lambda chars, taken: "athlete")
        self.assertEqual(rows, [{"name": "정민", "is_npc": False, "character_id": "scholar"},
                                {"name": "로봇", "is_npc": True, "character_id": "athlete"}])
        self.popup.ask_setup = lambda validator: None
        self.assertIsNone(self.input.run_setup(D.CHARACTERS))

    def test_invest(self):
        me = player(player_money=1000, is_npc=False)
        self.popup.ask_invest = lambda *a: ("tuntun", "500")
        self.assertEqual(self.input.ask_invest(me, D.COMPANIES), {"company_id": "tuntun", "amount": 500})
        self.popup.ask_invest = lambda *a: ("tuntun", 0)          # 0 = 건너뛰기
        self.assertIsNone(self.input.ask_invest(me, D.COMPANIES))
        self.popup.ask_invest = lambda *a: ("tuntun", 5000)       # 보유 금액 초과 (이중 방어)
        self.assertIsNone(self.input.ask_invest(me, D.COMPANIES))

    def test_job_exam_business(self):
        me = player(is_npc=False, player_stats={"지력": 10, "체력": 10, "센스": 10})
        self.popup.ask_job = lambda *a: None                     # 값 없이 닫힘 → 고를 수 있는 첫 직업
        self.assertEqual(self.input.ask_job(me, D.JOBS), "freelancer")
        self.assertIsNone(self.input.ask_job(me, D.JOBS, allow_keep=True))
        self.popup.ask_exam = lambda *a: None                    # 시간 초과
        self.assertIsNone(self.input.ask_exam_answer(me, D.EXAM[0], 16, "첫 도전"))
        self.popup.ask_exam = lambda *a: 2
        self.assertEqual(self.input.ask_exam_answer(me, D.EXAM[0], 16, "첫 도전"), 2)
        self.popup.ask_switch_business = lambda *a: "youtube"   # 같은 업종 → 바꾸지 않음
        rich = player(is_npc=False, player_money=5000)
        self.assertIsNone(self.input.ask_switch_business(rich, D.BUSINESSES, "youtube", "nft", 2))
        self.popup.ask_switch_business = lambda *a: "nft"
        self.assertEqual(self.input.ask_switch_business(rich, D.BUSINESSES, "youtube", "nft", 2), "nft")

    def test_artwork_full_studio_must_sell(self):
        studio = [{"id": "a", "title": "A", "price": 300}, {"id": "b", "title": "B", "price": 100}]
        self.popup.ask_artwork = lambda *a: None
        self.assertEqual(self.input.ask_artwork(player(), {"id": "c", "title": "C", "price": 30}, studio), "c")
        self.assertIsNone(self.input.ask_artwork(player(), {"id": "c", "title": "C", "price": 30}, studio[:1]))


if __name__ == "__main__":
    unittest.main()
