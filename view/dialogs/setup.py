"""
view/dialogs/setup.py  —  게임 준비 창

  SetupDialog      게임 설정 (플레이어 수, 이름, NPC 지정)        FR-03-01, FR-03-03
  CharacterDialog  캐릭터 선택 (얼굴·능력치·특성, 중복 선택 불가) FR-01-08, FR-02-07
"""
from __future__ import annotations

from PyQt5.QtWidgets import (QLabel, QLineEdit, QCheckBox, QRadioButton, QButtonGroup, QGridLayout,
                             QHBoxLayout, QVBoxLayout, QMessageBox)

from common.constants import STAT_NAMES
from common.adapter import read_character
from view import style
from view.painter_kit import FaceWidget
from view.widgets import title, quiet, button, card_frame, StatBar, chip
from view.dialogs.base import BaseDialog

MAX_PLAYERS = 4
MIN_PLAYERS = 2
NAME_MAX_LEN = 10


class SetupDialog(BaseDialog):
    """게임 설정: 인원(2~4, 라디오 버튼만 허용) + 이름 + NPC 지정"""

    def __init__(self, validator, parent=None):
        super().__init__(parent, 460, "게임 설정")
        self.validator = validator     # Input이 넣어 주는 검사 함수: rows → 오류 메시지("" = 통과)

        # 인원 선택 (2.4: 2~4 범위 내 지정된 UI 조작만 허용)
        self.count_group = QButtonGroup(self)
        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("플레이어 수"))
        for n in range(MIN_PLAYERS, MAX_PLAYERS + 1):
            radio = QRadioButton(f"{n}명")
            self.count_group.addButton(radio, n)
            count_row.addWidget(radio)
        count_row.addStretch(1)
        self.count_group.button(MIN_PLAYERS).setChecked(True)
        self.count_group.buttonClicked.connect(lambda _: self._apply_count())

        # 플레이어별 이름 + NPC 체크
        grid = QGridLayout()
        grid.setVerticalSpacing(6)
        self.rows = []
        for i in range(MAX_PLAYERS):
            label = QLabel(f"플레이어 {i + 1}")
            label.setStyleSheet(f"color: {style.player_color_hex(i)}; font-weight: bold;")
            name = QLineEdit()
            name.setMaxLength(NAME_MAX_LEN)
            name.setPlaceholderText("이름 (1~10자)")
            npc = QCheckBox("NPC")
            npc.toggled.connect(lambda on, e=name: on and not e.text() and e.setText("알파"))
            grid.addWidget(label, i, 0)
            grid.addWidget(name, i, 1)
            grid.addWidget(npc, i, 2)
            self.rows.append((label, name, npc))

        ok = button("다음: 캐릭터 선택", role="primary")
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        cancel = button("그만두기")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addWidget(cancel)
        buttons.addWidget(ok, 1)

        self.body.addWidget(title("누구누구 인생을 살아 볼까요?", 26))
        self.body.addWidget(quiet("2~4명이 함께해요. NPC(컴퓨터)는 1명까지 정할 수 있어요."))
        self.body.addLayout(count_row)
        self.body.addLayout(grid)
        self.body.addLayout(buttons)
        self._apply_count()

    def player_count(self) -> int:
        return self.count_group.checkedId()

    def _apply_count(self) -> None:
        n = self.player_count()
        for i, widgets in enumerate(self.rows):
            for w in widgets:
                w.setVisible(i < n)
        self.adjustSize()

    def values(self) -> list:
        n = self.player_count()
        return [{"name": name.text().strip(), "is_npc": npc.isChecked()}
                for _, name, npc in self.rows[:n]]

    def accept(self) -> None:
        message = self.validator(self.values()) if self.validator else ""
        if message:                       # 잘못된 입력이면 창을 닫지 않고 경고만
            QMessageBox.warning(self, "입력 확인", message)
            return
        super().accept()


class CharacterDialog(BaseDialog):
    """캐릭터 선택: 얼굴·능력치·고유 특성 표시, 이미 고른 캐릭터는 비활성화"""

    def __init__(self, player_name: str, characters, taken_ids, color=None, parent=None):
        super().__init__(parent, 640, "캐릭터 선택")
        self.selected_id = None

        grid = QGridLayout()
        grid.setSpacing(12)
        for i, raw in enumerate(characters):
            c = read_character(raw)
            card = card_frame(f"char{i}")
            box = QVBoxLayout(card)
            box.setContentsMargins(12, 10, 12, 10)
            head = QHBoxLayout()
            head.addWidget(FaceWidget(c.name, color or style.player_color_hex(i), size=52))
            name_col = QVBoxLayout()
            name_col.addWidget(title(c.name, 20))
            name_col.addWidget(quiet(f"능력치 합 {sum(c.stats.values())}", 11))
            head.addLayout(name_col, 1)
            box.addLayout(head)
            for stat in STAT_NAMES:
                bar = StatBar(stat)
                bar.set_value(c.stats.get(stat, 0))
                box.addWidget(bar)
            trait = QLabel(f"<b>특성</b> {c.trait or '없음'}")
            trait.setWordWrap(True)
            trait.setStyleSheet("font-size: 12px;")
            box.addWidget(trait)
            if c.good_jobs:
                box.addWidget(chip(f"잘 맞는 직업: {c.good_jobs}", "#E4F6EA", "#1E7A45"))
            pick = button("이 캐릭터로!", role="primary", min_height=34)
            if c.id in taken_ids:   # 2.5 예외: 이미 선택된 캐릭터 → 버튼 비활성화
                pick.setEnabled(False)
                pick.setText("이미 선택된 캐릭터입니다.")
            pick.clicked.connect(lambda _, cid=c.id: self._choose(cid))
            box.addWidget(pick)
            grid.addWidget(card, i // 2, i % 2)

        self.body.addWidget(title(f"{player_name}님, 캐릭터를 고르세요", 24))
        self.body.addWidget(quiet("네 캐릭터 모두 능력치 합은 120이에요. 특성이 직업 선택을 가릅니다."))
        self.body.addLayout(grid)

    def _choose(self, cid) -> None:
        self.selected_id = cid
        self.accept()
