"""
run_demo.py  —  내 모듈(View·Input·NPC)만으로 게임 흐름을 돌려 보는 실행 파일

    python run_demo.py

⚠ dev_stub의 가짜 Model/Controller를 쓴다. 팀원 코드가 오면 진짜 main.py에서
  Window, Input, NPC를 만들어 팀원의 GameController에 넘겨주면 된다.
"""
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from view import Window, install_exception_hook
from view.style import apply_app_font
from user_input import Input
from npc import NPC
from dev_stub.fake_model import FakeModel
from dev_stub.fake_controller import FakeController


def main() -> None:
    app = QApplication(sys.argv)
    apply_app_font(app)

    window = Window()
    install_exception_hook(window)      # NFR-04: 오류가 나도 꺼지지 않게

    controller = FakeController(window, Input(window), NPC(), FakeModel())
    window.show()
    QTimer.singleShot(0, controller.start)   # 창이 뜬 뒤 설정 창을 띄운다
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
