"""
main.py  —  인생마불 실행 파일

    python main.py          진짜 게임 (팀원 Controller·Model이 완성되면)
    python run_demo.py      지금 바로 돌려 보는 데모 (팀장 모듈 + 가짜 Model)
"""
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from view import Window, install_exception_hook
from view.style import apply_app_font
from user_input import Input
from npc import NPC
from controller.game_controller import GameController


def main() -> None:
    app = QApplication(sys.argv)
    apply_app_font(app)
    window = Window()
    install_exception_hook(window)                 # 처리하지 못한 오류 → 오류 창만 띄우고 계속

    controller = GameController(window, Input(window), NPC(), quick="--quick" in sys.argv)
    window.show()

    def start() -> None:
        try:
            controller.start()
        except NotImplementedError:
            window.popup_view.show_message("Controller가 아직 만들어지지 않았습니다.\n"
                                           "지금은 python run_demo.py 로 데모를 볼 수 있습니다.", "준비 중")
            window.close()

    QTimer.singleShot(0, start)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
