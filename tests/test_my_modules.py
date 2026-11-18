"""
tests/test_my_modules.py  —  내 모듈 단위 테스트 (python -m unittest discover tests)

  TestBoardCoords  : 보드 좌표·경로 계산 (BoardView의 순수 함수)
  TestInputCheck   : 2.5 예외 처리 표의 입력 검사 메시지
  TestNPC          : TC-05 NPC가 이기는 방향으로 판단하는지
  TestFullGame     : 가짜 Model/Controller로 게임 한 판을 끝까지 자동 진행 (화면 없이)
"""
import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")       # 화면 없이 Qt 실행
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from view.board_view import build_tile_coords, make_path                       # noqa: E402
from user_input.input_handler import (validate_setup, validate_invest_text,    # noqa: E402
                                      parse_amount, MSG_NAME_EMPTY, MSG_NAME_DUP,
                                      MSG_NOT_NUMBER, MSG_OVER_MONEY, MSG_NPC_LIMIT)
from npc import NPC                                                              # noqa: E402
from common.adapter import read_player                                          # noqa: E402


def player(**kw):
    base = {"player_id": 0, "player_name": "NPC", "player_money": 3_000_000, "player_age": 2,
            "player_happiness": 50, "player_stats": {"지력": 50, "체력": 50, "센스": 50},
            "player_lap": 4, "is_npc": True}
    base.update(kw)
    return base


class TestBoardCoords(unittest.TestCase):
    def test_28_unique_border_cells(self):
        coords = build_tile_coords()
        self.assertEqual(len(coords), 28)
        self.assertEqual(len(set(coords)), 28)
        for r, c in coords:                       # 모두 8×8 테두리 위
            self.assertTrue(r in (0, 7) or c in (0, 7))

    def test_start_is_bottom_right_and_neighbors_touch(self):
        coords = build_tile_coords()
        self.assertEqual(coords[0], (7, 7))
        for a, b in zip(coords, coords[1:] + coords[:1]):   # 이웃 칸은 상하좌우로 붙어 있다
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)

    def test_path_wraps_around(self):
        self.assertEqual(make_path(26, 4), [27, 0, 1, 2])
        self.assertEqual(make_path(1, -3), [0, 27, 26])


class TestInputCheck(unittest.TestCase):
    def test_setup_messages(self):
        self.assertIn(MSG_NAME_EMPTY, validate_setup([{"name": " ", "is_npc": False}, {"name": "B", "is_npc": False}]))
        self.assertIn(MSG_NAME_DUP, validate_setup([{"name": "A", "is_npc": False}, {"name": "A", "is_npc": False}]))
        self.assertEqual(MSG_NPC_LIMIT, validate_setup([{"name": "A", "is_npc": True}, {"name": "B", "is_npc": True}]))
        self.assertEqual("", validate_setup([{"name": "A", "is_npc": False}, {"name": "B", "is_npc": True}]))

    def test_invest_messages(self):
        self.assertEqual(MSG_NOT_NUMBER, validate_invest_text("abc", 1_000_000))
        self.assertEqual(MSG_OVER_MONEY, validate_invest_text("2000000", 1_000_000))
        self.assertEqual("", validate_invest_text("1,000,000원", 1_000_000))
        self.assertEqual(500_000, parse_amount(" 500,000 "))


class TestNPC(unittest.TestCase):
    def setUp(self):
        self.npc = NPC(seed=1)

    def test_job_picks_best_eligible(self):
        jobs = [{"id": "doctor", "salary": 900_000, "requirements": {"지력": 72}},
                {"id": "office", "salary": 500_000, "requirements": {"지력": 50}},
                {"id": "part", "salary": 300_000, "requirements": {}}]
        self.assertEqual("office", self.npc.ask_job(player(), jobs))          # 의사는 조건 미달
        self.assertEqual("doctor", self.npc.ask_job(player(player_stats={"지력": 80}), jobs))

    def test_invest_keeps_reserve_and_is_integer(self):
        amount = self.npc.ask_invest(player(player_money=3_000_000))
        self.assertIsInstance(amount, int)
        self.assertLessEqual(amount, 3_000_000 - self.npc.reserve_money(3_000_000))
        self.assertEqual(0, amount % 10_000)
        self.assertEqual(0, self.npc.ask_invest(player(player_money=400_000)))   # 안전 자금 이하
        self.assertEqual(0, self.npc.ask_invest(player(), expected_return_percent=0))

    def test_invest_more_when_losing(self):
        me = player(player_id=0)
        rich = player(player_id=1, player_money=9_000_000, is_npc=False)
        poor = player(player_id=1, player_money=1_000_000, player_happiness=10, is_npc=False)
        self.assertGreater(self.npc.ask_invest(me, [rich]), self.npc.ask_invest(me, [poor]))

    def test_shop_skips_when_poor_and_ignores_capped_happiness(self):
        items = [{"name": "여행", "price": 800_000, "happiness": 15}]
        self.assertIsNone(self.npc.ask_shop(player(player_money=600_000), items))
        self.assertEqual(0, self.npc.ask_shop(player(player_happiness=50), items))
        self.assertIsNone(self.npc.ask_shop(player(player_happiness=100), items))  # 이미 최대

    def test_choice_picks_higher_score(self):
        options = [{"name": "안정", "money": 300_000}, {"name": "도전", "money": -100_000, "happiness": 10}]
        self.assertEqual(1, self.npc.ask_choice(player(), options=options))

    def test_character_highest_total_not_taken(self):
        chars = [{"id": "a", "stats": {"지력": 50}}, {"id": "b", "stats": {"지력": 90}}]
        self.assertEqual("b", self.npc.choose_character(chars, []))
        self.assertEqual("a", self.npc.choose_character(chars, ["b"]))


class TestFullGame(unittest.TestCase):
    """창 없이 게임 한 판: 사람 1명(자동 클릭) + NPC 1명이 끝까지 가는지"""

    def test_game_runs_to_result(self):
        from PyQt5.QtCore import QTimer
        from PyQt5.QtWidgets import QApplication
        import view.board_view as bv
        import view.dice_view as dv
        from view import Window
        from user_input import Input
        from dev_stub.fake_model import FakeModel
        from dev_stub.fake_controller import FakeController

        app = QApplication.instance() or QApplication([])
        bv.MOVE_STEP_MS, dv.FRAME_MS = 1, 1          # 테스트는 빠르게

        window = Window()
        popup = window.popup_view
        results = []
        popup.ask_setup = lambda validator: [{"name": "철수", "is_npc": False}, {"name": "컴퓨터", "is_npc": True}]
        popup.ask_character = lambda name, chars, taken: next(c["id"] for c in chars if c["id"] not in taken)
        popup.ask_job = lambda name, jobs, stats: jobs[-1]["id"]
        popup.ask_shop = lambda name, money, items: None
        popup.ask_invest = lambda name, money, validator: "100000"
        popup.show_event = lambda *a, **k: None
        popup.show_result = lambda ranking: (results.append(ranking), app.quit())

        user_input = Input(window)
        controller = FakeController(window, user_input, NPC(think_delay_ms=1, seed=3), FakeModel(seed=7))

        def human_plays():   # 사람 차례면 투자 버튼 → 주사위 버튼을 누른다
            if window.dice_view.invest_button.isEnabled():
                window.dice_view.invest_button.click()
            if window.dice_view.roll_button.isEnabled():
                window.dice_view.roll_button.click()

        clicker = QTimer()
        clicker.timeout.connect(human_plays)
        clicker.start(2)
        QTimer.singleShot(60_000, app.quit)            # 안전장치
        self.assertTrue(controller.start())
        app.exec_()
        clicker.stop()

        self.assertEqual(1, len(results), "결과 화면까지 가지 못함")
        self.assertTrue(controller.model.all_finished())
        names = [r["name"] for r in results[0]]
        self.assertCountEqual(["철수", "컴퓨터"], names)
        self.assertEqual([read_player(p).stage for p in controller.model.players], ["노년기", "노년기"])


if __name__ == "__main__":
    unittest.main()
