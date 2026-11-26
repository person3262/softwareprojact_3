"""
tests/helpers.py  —  테스트 공통 준비: 화면 없이 Qt 실행 + 가짜 플레이어 만들기
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")      # 창을 실제로 띄우지 않는다
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication                    # noqa: E402

APP = QApplication.instance() or QApplication([])


def app():
    return APP


def player(**kw) -> dict:
    """adapter가 읽는 이름(계획서 3.3)으로 만든 가짜 플레이어. 필요한 값만 덮어쓴다."""
    base = {"player_id": 0, "player_name": "로봇", "player_money": 3000, "player_happiness": 50,
            "player_age": 2, "player_lap": 2, "player_stats": {"지력": 50, "체력": 50, "센스": 50},
            "is_npc": True, "job_state": "none"}
    base.update(kw)
    return base
