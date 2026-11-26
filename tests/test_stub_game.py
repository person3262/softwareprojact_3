"""가짜 Model·Controller로 한 판을 끝까지 자동 진행 — View·Input·NPC가 함께 돌아가는지 (화면 없이)"""
import time
import unittest

from tests.helpers import app
from view import Window
from dev_stub.fake_controller import FakeController

ROWS = [{"name": n, "is_npc": True, "character_id": c}
        for n, c in [("가", "scholar"), ("나", "athlete"), ("다", "dreamer"), ("라", "normal")]]


def quiet_window():
    """모달 창이 테스트를 멈추지 않게 show_* 창을 가짜로 바꾼 Window"""
    w = Window()
    shown = []
    for name in ("show_event", "show_exam_npc", "show_message", "show_warning", "show_error"):
        setattr(w.popup_view, name, lambda *a, _n=name, **k: shown.append(_n))
    w.popup_view.show_result = lambda ranking: False
    return w, shown


class TestStubGame(unittest.TestCase):
    def run_game(self, seed, quick):
        app()
        w, shown = quiet_window()
        c = FakeController(w, quick=quick, seed=seed, fast=True)
        done = {}
        c.finished_callback = lambda game: done.setdefault("game", game)
        c.start([dict(r) for r in ROWS])
        end = time.time() + 60
        while "game" not in done and time.time() < end:
            app().processEvents()
        w.close()
        return done.get("game"), shown

    def test_full_games_finish(self):
        for seed, quick in ((1, True), (2, False), (3, False)):
            with self.subTest(seed=seed, quick=quick):
                game, shown = self.run_game(seed, quick)
                self.assertIsNotNone(game, "게임이 끝나지 않았다")
                self.assertTrue(all(p.finished for p in game.players))
                self.assertTrue(all(p.player_job or p.job_state == "student" for p in game.players))
                ranking = game.ranking()
                self.assertEqual(len(ranking), 4)
                self.assertTrue(all(r["score"] == r["money"] + r["happiness"] * 10 for r in ranking))
                self.assertGreater(len(shown), 20)

    def test_human_player_clicks_through(self):
        """사람 1명 + NPC 3명: 사람 차례에는 버튼을 '누르고' 창에는 정해진 답을 한다"""
        app()
        from PyQt5.QtCore import QTimer
        w, shown = quiet_window()
        popup = w.popup_view
        popup.ask_job = lambda name, jobs, stats, exclude=(), allow_keep=False, heading="": None
        popup.ask_exam = lambda name, q, *a: q["answer"]
        popup.ask_confirm = lambda *a, **k: True
        popup.ask_business = lambda *a, **k: "nft"
        popup.ask_switch_business = lambda *a, **k: None
        popup.ask_gig = lambda name, cards, *a: cards[0]["id"]
        popup.ask_artwork = lambda *a, **k: None
        popup.ask_shop = lambda *a, **k: None
        popup.ask_invest = lambda *a, **k: ("tuntun", 100)
        popup.ask_choice = lambda *a, **k: 0
        c = FakeController(w, quick=True, seed=11, fast=True)
        clicks = {"roll": 0, "invest": 0, "end": 0}
        dice = w.dice_view
        original_unlock, original_actions = c.input.unlock, c.input.unlock_actions

        def unlock():
            original_unlock()
            clicks["roll"] += 1
            QTimer.singleShot(0, dice.roll_button.click)

        def unlock_actions(can_invest=False):
            original_actions(can_invest)
            if dice.invest_button.isEnabled():
                clicks["invest"] += 1
                QTimer.singleShot(0, dice.invest_button.click)
                return
            clicks["end"] += 1
            QTimer.singleShot(0, dice.roll_button.click)

        c.input.unlock, c.input.unlock_actions = unlock, unlock_actions
        done = {}
        c.finished_callback = lambda game: done.setdefault("game", game)
        rows = [{"name": "정민", "is_npc": False, "character_id": "scholar"}] + [dict(r) for r in ROWS[1:]]
        c.start(rows)
        end = time.time() + 60
        while "game" not in done and time.time() < end:
            app().processEvents()
        w.close()
        game = done.get("game")
        self.assertIsNotNone(game, "사람이 낀 게임이 끝나지 않았다")
        me = game.players[0]
        self.assertTrue(me.finished)
        self.assertGreater(clicks["roll"], 5)
        self.assertGreater(clicks["end"], 0)
        self.assertIsNotNone(me.player_job)

    def test_exam_pass_makes_doctor(self):
        app()
        w, _ = quiet_window()
        c = FakeController(w, seed=5, fast=True)
        c.start([dict(r) for r in ROWS])
        p = c.game.players[0]
        c.game.set_job(p, "doctor")
        self.assertEqual(p.job_state, "student")
        c.npc.ask_exam_answer = lambda player, q, *a: q["answer"]       # 무조건 맞힌다
        c.exam(p)
        self.assertEqual((p.job_state, p.player_job["id"]), ("employed", "doctor"))
        w.close()


if __name__ == "__main__":
    unittest.main()
