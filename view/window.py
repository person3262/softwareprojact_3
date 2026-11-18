"""
view/window.py  —  Window: 최상위 메인 창 (FR-02-01)

화면 분할
  ┌──────────────────────────┬───────────────┐
  │                          │  PanelView    │
  │       BoardView          │ (상태창+기록) │
  │   (보드판 + PieceView)   ├───────────────┤
  │                          │  DiceView     │
  └──────────────────────────┴───────────────┘
  + PopupView (필요할 때 띄우는 창들)

Controller는 화면을 바꿀 때 Window의 함수만 부르면 된다. (아래 '외부 공개 함수')
Window가 알맞은 하위 View에게 일을 넘겨준다. → 팀원은 View 내부 구조를 몰라도 된다.
"""
from __future__ import annotations

import sys
import traceback

from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QMessageBox

from common.adapter import read_player
from view.board_view import BoardView
from view.panel_view import PanelView
from view.dice_view import DiceView
from view.popup_view import PopupView


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("인생마불")
        self.resize(1180, 800)

        self.board_view = BoardView()
        self.panel_view = PanelView()
        self.dice_view = DiceView()
        self.popup_view = PopupView(self)

        right = QVBoxLayout()
        right.addWidget(self.panel_view, 1)
        right.addWidget(self.dice_view)

        right_box = QWidget()
        right_box.setLayout(right)
        right_box.setFixedWidth(380)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.addWidget(self.board_view, 1)
        layout.addWidget(right_box)
        self.setCentralWidget(central)

    # ═══════════════ 외부 공개 함수 (Controller가 부름) ═══════════════
    # 게임 준비
    def set_board(self, tiles) -> None:
        """Model Board의 타일 28개로 보드 칸을 그린다."""
        self.board_view.set_tiles(tiles)

    def set_players(self, players) -> None:
        """게임 시작 시 1번: 말과 상태창 카드를 만든다."""
        self.board_view.set_pieces(players)
        self.panel_view.set_players(players)

    # 턴 진행
    def set_current_player(self, player) -> None:
        info = read_player(player)
        self.board_view.set_current_player(info.id)
        self.panel_view.set_current_player(player)
        self.board_view.set_center_text(f"{info.name}의 차례 · {info.stage}")

    def refresh(self, players) -> None:
        """Model 값이 바뀐 뒤 부르면 상태창과 말 위치를 최신 값으로 덮어쓴다."""
        self.panel_view.update_players(players)
        self.board_view.update_pieces(players)

    def show_dice(self, d1: int, d2: int, on_done=None) -> None:
        self.dice_view.show_result(d1, d2, on_done)

    def move_piece(self, player_id, from_index: int, steps: int, on_done=None) -> None:
        self.board_view.move_piece(player_id, from_index, steps, on_done)

    def set_roll_enabled(self, enabled: bool) -> None:
        self.dice_view.set_roll_enabled(enabled)

    def set_invest_enabled(self, enabled: bool) -> None:
        self.dice_view.set_invest_enabled(enabled)

    def add_log(self, text: str) -> None:
        self.panel_view.add_log(text)

    # 알림창 (묻는 창은 Input을 통해서 띄운다)
    def show_event(self, event, player_name: str = "", auto_close_ms: int = None) -> None:
        self.popup_view.show_event(event, player_name, auto_close_ms)

    def show_result(self, ranking) -> None:
        self.popup_view.show_result(ranking)

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
