"""View 확인 — 좌표·숫자 표시 같은 순수 함수 + 모든 창이 오류 없이 만들어지는지"""
import unittest

from tests.helpers import app
from common.adapter import read_player, pick, read_tile
from view import Window
from view.board_view import build_tile_coords, make_path
from view.center_view import stage_text
from view.style import format_money, format_money_delta
from view.panel_view import rank_of


class TestBoard(unittest.TestCase):
    def test_28_border_cells_clockwise(self):
        coords = build_tile_coords()
        self.assertEqual(len(set(coords)), 28)
        self.assertEqual(coords[0], (7, 7))                     # 0번 = 오른쪽 아래
        for a, b in zip(coords, coords[1:] + coords[:1]):      # 이웃 칸은 붙어 있다
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)

    def test_path_wraps(self):
        self.assertEqual(make_path(26, 4), [27, 0, 1, 2])


class TestText(unittest.TestCase):
    def test_money(self):
        self.assertEqual(format_money(4180), "4,180만원")
        self.assertEqual(format_money(12640), "1억 2,640만원")
        self.assertEqual(format_money(0), "0원")
        self.assertEqual(format_money(-300), "-300만원")        # 빚은 음수로
        self.assertEqual(format_money_delta(500), "+500만원")

    def test_stage_text_and_rank(self):
        self.assertEqual(stage_text(read_player({"player_age": 2, "player_lap": 3})), "성년기 3바퀴")
        infos = [read_player({"player_id": i, "player_money": m, "player_happiness": h})
                 for i, (m, h) in enumerate([(1000, 10), (500, 70), (1100, 0)])]
        self.assertEqual(rank_of(infos), {1: 1, 2: 2, 0: 3})       # 총점 1200 > 1100 = 1100 → 같으면 돈 많은 쪽 앞

    def test_adapter_reads_any_names(self):
        class Teammate:                       # 팀원 Model 속성 이름이 조금 달라도 읽는다
            name, money, happiness, stage = "하늘", 700, 5, "청년기"
        info = read_player(Teammate())
        self.assertEqual((info.name, info.money, info.stage, info.score), ("하늘", 700, "청년기", 750))
        self.assertIsNone(pick("문자열", ("title",)))           # str 함수가 잡히지 않는다
        self.assertEqual(read_tile("golden_key").name, "황금열쇠")


class TestWindowAndDialogs(unittest.TestCase):
    def test_window_api(self):
        app()
        from dev_stub.fake_model import FakeGame
        rows = [{"name": "정민", "is_npc": False, "character_id": "scholar"},
                {"name": "로봇", "is_npc": True, "character_id": "normal"}]
        game = FakeGame(rows)
        w = Window()
        w.set_board(game.board)
        w.set_players(game.players)
        w.set_current_player(game.players[1])
        game.players[1].player_money = -250
        w.refresh(game.players)
        w.set_round(3)
        w.show_news("원숭이 NFT가 10억에 팔렸다!")
        w.show_income(0, 700, 7)
        w.set_end_mode(True)
        self.assertEqual(w.dice_view.roll_button.text(), "턴 마치기")
        self.assertIn("NFT", w.center.ticker.text())
        w.close()

    def test_every_dialog_builds(self):
        app()
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
        from ui_gallery import build_dialogs
        for name, make in build_dialogs():
            with self.subTest(dialog=name):
                dlg = make()
                dlg.deleteLater()


if __name__ == "__main__":
    unittest.main()
