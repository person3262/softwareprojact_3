"""
run_demo.py  —  팀장 모듈(View·Input·NPC)을 가짜 Model/Controller(dev_stub)로 끝까지 돌려 보는 데모

    python run_demo.py            빠른 모드 (단계마다 1바퀴, 발표 시연용)
    python run_demo.py --full     규칙대로 7바퀴

⚠ dev_stub은 팀장이 화면을 확인하려고 만든 '대역'이다. 진짜 게임은 main.py에서
  팀원의 GameController가 Window·Input·NPC를 받아서 돌린다.
"""
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from view import Window, install_exception_hook
from view.style import apply_app_font
from dev_stub.fake_controller import FakeController


def main() -> None:
    app = QApplication(sys.argv)
    apply_app_font(app)

    window = Window()
    install_exception_hook(window)      # 오류가 나도 프로그램을 끄지 않고 오류 창만 띄운다
    controller = FakeController(window, quick="--full" not in sys.argv)
    window.show()
    QTimer.singleShot(0, controller.start)   # 창이 뜬 뒤 게임 설정 창을 띄운다
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
