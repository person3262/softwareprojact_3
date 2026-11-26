"""
view/window.py  —  Window: 최상위 메인 창 (FR-02-01)

화면 분할
  SkyBackground (창 전체 하늘: 지금 차례인 사람의 인생 단계를 따라 바뀐다)
  ┌──────────────────────────────────┬─────────────────┐
  │ BoardView (28칸 + 말)            │  PanelView       │
  │   └ CenterPanel                  │  (라운드·유행    │
  │       로고, 인생 지도, 차례 배너  │   + 플레이어 카드│
  │       DiceView, 속보 띠           │   + 진행 기록)   │
  └──────────────────────────────────┴─────────────────┘
  + PopupView (필요할 때 띄우는 창들)

Controller는 화면을 바꿀 때 Window의 함수만 부르면 된다. (아래 '외부 공개 함수')
Window가 알맞은 하위 View에게 일을 넘겨준다. → 팀원은 View 내부 구조를 몰라도 된다.
"""
from __future__ import annotations

import sys
import traceback

from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QMessageBox, QScrollArea, QFrame

from common.adapter import read_player
from view.board_view import BoardView
from view.panel_view import PanelView
from view.popup_view import PopupView
from view.sky_view import SkyBackground


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("인생마불")
        self.resize(1400, 900)
        self.setMinimumSize(1180, 760)

        self.board_view = BoardView()
        self.panel_view = PanelView()
        self.popup_view = PopupView(self)
        self.center = self.board_view.center
        self.dice_view = self.center.dice_view          # 주사위·버튼은 보드 가운데에 있다

        scroll = QScrollArea()                           # 플레이어가 4명이면 카드가 길어질 수 있다
        scroll.setWidget(self.panel_view)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setFixedWidth(400)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        scroll.viewport().setAutoFillBackground(False)
        self.panel_view.setAutoFillBackground(False)

        self.sky = SkyBackground()                       # 창 전체 바탕
        layout = QHBoxLayout(self.sky)
        layout.setContentsMargins(18, 16, 14, 16)
        layout.setSpacing(16)
        layout.addWidget(self.board_view, 1)
        layout.addWidget(scroll)
        self.setCentralWidget(self.sky)

    # ═══════════════ 외부 공개 함수 (Controller가 부름) ═══════════════
    # 게임 준비
    def set_board(self, tiles) -> None:
        """Model Board의 타일 28개로 보드 칸을 그린다. (Tile 객체, 딕셔너리, "luck" 같은 문자열 모두 가능)"""
        self.board_view.set_tiles(tiles)

    def set_players(self, players) -> None:
        """게임 시작 시 1번: 말과 상태창 카드를 만든다."""
        self.board_view.set_pieces(players)
        self.panel_view.set_players(players)

    # 턴 진행
    def set_current_player(self, player) -> None:
        """차례가 바뀔 때: 말 강조, 카드 강조, 가운데 '○○의 차례!' 배너, 하늘을 그 사람의 인생 단계로"""
        self.board_view.set_current_player(player)
        self.panel_view.set_current_player(player)
        self.sky.set_stage(read_player(player).stage_index)
        self.dice_view.reset()

    def refresh(self, players) -> None:
        """Model 값이 바뀐 뒤 부르면 상태창·말 위치·인생 지도를 최신 값으로 덮어쓴다."""
        self.panel_view.update_players(players)
        self.board_view.update_pieces(players)

    def set_round(self, number: int) -> None:
        self.panel_view.set_round(number)

    def show_dice(self, d1: int, d2: int, on_done=None) -> None:
        self.dice_view.show_result(d1, d2, on_done)

    def move_piece(self, player_id, from_index: int, steps: int, on_done=None) -> None:
        self.board_view.move_piece(player_id, from_index, steps, on_done)

    def show_income(self, player_id, money: int, happiness: int) -> None:
        """매 턴 수입을 '+700만원 / 행복 +7'처럼 떠오르는 숫자로 보여 준다. (FR-02-10) 창을 막지 않는다."""
        self.center.show_income(money, happiness)

    def set_roll_enabled(self, enabled: bool) -> None:
        self.dice_view.set_roll_enabled(enabled)

    def set_end_mode(self, on: bool) -> None:
        """True면 큰 버튼이 '턴 마치기'가 된다. Input.unlock_actions()가 부른다."""
        self.dice_view.set_end_mode(on)

    def set_invest_enabled(self, enabled: bool) -> None:
        self.dice_view.set_invest_enabled(enabled)

    def add_log(self, text: str) -> None:
        self.panel_view.add_log(text)

    # 속보와 유행 (FR-02-13, FR-02-15)
    def show_news(self, headline: str) -> None:
        """속보 띠에 소식을 올리고 기록창에도 남긴다. 창을 막지 않는다."""
        self.center.ticker.add_news(headline)
        self.add_log(f"[속보] {headline}")

    def set_trend(self, text: str) -> None:
        """사업가 유행 표시. 예) '지금 유행: NFT 갤러리 (2라운드 남음)' — 오른쪽 위 유행 배지에 보인다."""
        if text:
            self.panel_view.set_trend(text)

    # 알림창 (묻는 창은 Input을 통해서 띄운다)
    def show_event(self, event, player_name: str = "", auto_close_ms: int = None) -> None:
        self.popup_view.show_event(event, player_name, auto_close_ms)

    def show_exam_npc(self, player_name, question, level, level_name, time_limit, answer, delay_ms=1000) -> None:
        """NPC가 국가고시를 볼 때 '고민 중...'을 보여 준 뒤 고른 답을 표시한다."""
        self.popup_view.show_exam_npc(player_name, question, level, level_name, time_limit, answer, delay_ms)

    def show_result(self, ranking) -> bool:
        """인생 성적표. '한 판 더!'를 누르면 True"""
        return self.popup_view.show_result(ranking)

    def show_message(self, text: str, title: str = "알림") -> None:
        self.popup_view.show_message(text, title)


def install_exception_hook(window: Window = None) -> None:
    """NFR-04: 처리되지 않은 오류가 나도 프로그램이 꺼지지 않고 오류 창만 띄운다.
    (PyQt5는 슬롯 안에서 예외가 나면 기본적으로 프로그램을 종료한다)"""
    def hook(exc_type, exc, tb):
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        print(text, file=sys.stderr)
        try:
            QMessageBox.critical(window, "오류", f"처리 중 오류가 발생했습니다.\n\n{exc_type.__name__}: {exc}")
        except Exception:
            pass
    sys.excepthook = hook
