"""
view/panel_view.py  —  PanelView: 오른쪽 플레이어 상태창 (FR-02-04)

모든 플레이어의 자금, 행복도, 능력치, 직업, 인생 단계를 항상 보여 준다. (2.4 입출력 명세)
  PanelView (QGroupBox "플레이어 상태창")
   ├─ 현재 차례 안내 줄
   ├─ PlayerCard × 플레이어 수   ← 한 명의 정보 카드
   └─ 기록창(로그)               ← "철수: 행운 칸 도착" 같은 진행 기록
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QGroupBox, QFrame, QLabel, QProgressBar, QVBoxLayout,
                             QHBoxLayout, QPlainTextEdit)

from common.adapter import (STAT_NAMES, STAT_MAX, HAPPINESS_MAX, PlayerInfo, read_player)
from view import style


def _bar(maximum: int, color: str, height: int = 12) -> QProgressBar:
    bar = QProgressBar()
    bar.setRange(0, maximum)
    bar.setFixedHeight(height)
    bar.setFormat("%v")
    bar.setAlignment(Qt.AlignCenter)
    bar.setStyleSheet(
        "QProgressBar { border: 1px solid #BBB; border-radius: 3px; background: #F2F2F2;"
        " font-size: 9px; color: #222; }"
        f"QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}")
    return bar


class PlayerCard(QFrame):
    """플레이어 한 명의 정보 카드"""

    def __init__(self, number: int, color_hex: str, parent=None):
        super().__init__(parent)
        self.number = number
        self.color_hex = color_hex
        self.setObjectName("card")

        self.header = QLabel()       # "1  철수 · 모범생"
        self.header.setStyleSheet("font-weight: bold;")
        self.stage_job = QLabel()    # "청년기 · 직업: 의사 · 완주 2회"
        self.money = QLabel()        # "자금: 3,200,000원"

        self.happy_bar = _bar(HAPPINESS_MAX, "#F1948A")
        self.stat_bars = {name: _bar(STAT_MAX, "#85C1E9", 10) for name in STAT_NAMES}

        happy_row = QHBoxLayout()
        happy_row.addWidget(QLabel("행복도"))
        happy_row.addWidget(self.happy_bar, 1)

        stat_row = QHBoxLayout()
        for name in STAT_NAMES:
            stat_row.addWidget(QLabel(name))
            stat_row.addWidget(self.stat_bars[name], 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        layout.addWidget(self.header)
        layout.addWidget(self.stage_job)
        layout.addWidget(self.money)
        layout.addLayout(happy_row)
        layout.addLayout(stat_row)
        self.set_current(False)

    def update_info(self, info: PlayerInfo) -> None:
        npc_tag = " [NPC]" if info.is_npc else ""
        character = f" · {info.character}" if info.character else ""
        self.header.setText(
            f"<span style='color:{self.color_hex}'>●</span> {self.number}  {info.name}{npc_tag}{character}")
        job = info.job or "없음"
        self.stage_job.setText(f"{info.stage} · 직업: {job} · 완주 {info.lap}회")

        if info.money < 0:   # 2.5 예외: 자금이 0 미만 → 빚으로 표시
            self.money.setText(f"자금: <b style='color:{style.BAD}'>{style.format_money(info.money)} (빚)</b>")
        else:
            self.money.setText(f"자금: <b>{style.format_money(info.money)}</b>")

        self.happy_bar.setValue(info.happiness)
        for name, bar in self.stat_bars.items():
            bar.setValue(info.stats.get(name, 0))

    def set_current(self, current: bool) -> None:
        """현재 차례인 플레이어 카드는 자기 색 굵은 테두리로 강조"""
        border = f"3px solid {self.color_hex}" if current else "1px solid #CCCCCC"
        bg = "#FFFFFF" if current else "#FAFAFA"
        self.setStyleSheet(f"QFrame#card {{ border: {border}; border-radius: 6px; background: {bg}; }}")


class PanelView(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("플레이어 상태창", parent)
        self.cards: dict = {}   # player_id → PlayerCard

        self.turn_label = QLabel("게임 준비 중")
        self.turn_label.setStyleSheet("font-weight: bold; padding: 2px;")

        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(6)

        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumBlockCount(300)
        self.log_box.setFixedHeight(90)
        self.log_box.setPlaceholderText("진행 기록")

        layout = QVBoxLayout(self)
        layout.addWidget(self.turn_label)
        layout.addLayout(self.cards_layout)
        layout.addStretch(1)
        layout.addWidget(self.log_box)

    def set_players(self, players) -> None:
        """게임 시작 시 플레이어 수만큼 카드를 만든다."""
        for card in self.cards.values():
            card.setParent(None)
        self.cards.clear()
        for order, p in enumerate(players):
            info = read_player(p)
            card = PlayerCard(order + 1, style.PLAYER_COLORS[order % len(style.PLAYER_COLORS)])
            card.update_info(info)
            self.cards_layout.addWidget(card)
            self.cards[info.id] = card

    def update_players(self, players) -> None:
        """수치가 바뀔 때마다 Model 값으로 카드 내용을 덮어쓴다. (3.4 핵심 프로세스 5번)"""
        for p in players:
            info = read_player(p)
            card = self.cards.get(info.id)
            if card is not None:
                card.update_info(info)

    def set_current_player(self, player) -> None:
        info = read_player(player)
        for pid, card in self.cards.items():
            card.set_current(pid == info.id)
        who = f"{info.name} (NPC)" if info.is_npc else info.name
        self.turn_label.setText(f"현재 차례: {who}")

    def add_log(self, text: str) -> None:
        self.log_box.appendPlainText(text)
