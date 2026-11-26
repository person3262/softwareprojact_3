"""
view/panel_view.py  —  PanelView: 오른쪽 상태창 (FR-02-04, FR-02-06, FR-02-07)

  ┌ [11라운드]  [지금 유행: NFT 갤러리 (2라운드 남음)]
  ├ PlayerCard × 인원수   얼굴 · 이름 · 순위 메달 · 돈(세어 올라감) · 행복 · 능력치 막대 · 수입 한 줄
  ├ 총점 규칙 한 줄
  └ 진행 기록
지금 차례인 사람의 카드는 그 사람 색 테두리로 바뀌고 조금 떠오른다.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtWidgets import (QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPlainTextEdit, QSizePolicy)

from common.constants import STAT_NAMES, STUDIO_SIZE
from common.adapter import read_player, PlayerInfo
from view import style
from view.widgets import chip, set_chip, StatBar, title, set_card_border, sticker_shadow, CountLabel
from view.painter_kit import FaceWidget, IconWidget, draw_crown
from view.center_view import stage_text

JOB_CHIP = ("#FFE3E7", "#B3263D")
STAGE_CHIP = ("#E1F0FF", "#1F5F9E")
MEDALS = {1: ("#FFD43B", "1"), 2: ("#DCE2F0", "2"), 3: ("#F4B07A", "3")}


def income_text(info: PlayerInfo) -> str:
    """카드 아래쪽 한 줄: 매 턴 수입이나 직업 장치 상태"""
    if info.job_state == "student":
        return f"의대생: 국가고시 {info.exam_level}단계 도전 중 (수입 없음)"
    if info.business:
        return f"업종 {info.business}, 매 턴 주사위로 실적"
    if not info.job:
        return "아직 직업이 없어요"
    text = f"매 턴 칸당 돈 {style.format_money(info.income_money)}, 행복 {info.income_happiness}"
    if info.gig:
        text += f" / 의뢰: {info.gig}"
    if info.job == "예술가" or info.artworks:
        text += f" / 작업실 {len(info.artworks)}/{STUDIO_SIZE}"
    return text


class Medal(QWidget):
    """순위 메달 (1위 금 + 왕관, 2위 은, 3위 동, 그 밖은 흰색)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rank = 0
        self.setFixedSize(40, 44)

    def set_rank(self, rank: int) -> None:
        self.rank = rank
        self.update()

    def paintEvent(self, event) -> None:
        if not self.rank:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        fill, _ = MEDALS.get(self.rank, ("#FFFFFF", str(self.rank)))
        c = QPointF(20, 26)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(style.INK)))
        p.drawEllipse(c + QPointF(0, 3), 15, 15)
        p.setPen(QPen(QColor(style.INK), 3))
        p.setBrush(QBrush(QColor(fill)))
        p.drawEllipse(c, 15, 15)
        p.setPen(QColor(style.INK))
        p.setFont(style.title_font(17))
        p.drawText(QRectF(c.x() - 15, c.y() - 15, 30, 30), Qt.AlignCenter, str(self.rank))
        if self.rank == 1:
            draw_crown(p, QRectF(c.x() - 10, 0, 20, 13), style.SUN)
        p.end()


class PlayerCard(QFrame):
    """플레이어 한 명의 정보 카드 (스티커)"""

    def __init__(self, number: int, color_hex: str, parent=None):
        super().__init__(parent)
        self.number = number
        self.color_hex = color_hex
        self.current = False
        self.setObjectName(f"pcard{number}")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sticker_shadow(self, 4)

        self.face = FaceWidget(color=color_hex, size=54)
        self.name = title("", 23, style.INK)
        self.npc_chip = chip("NPC", "#A66BFF", "white", bold=True)
        self.character = QLabel("")
        self.character.setStyleSheet(f"color: {style.TEXT_QUIET}; font-size: 12px;")
        self.medal = Medal()
        self.chip_job = chip("", *JOB_CHIP, bold=True)
        self.chip_stage = chip("", *STAGE_CHIP, bold=True)
        self.turn_tag = chip("내 차례", color_hex, "white", bold=True, size=12)
        self.turn_tag.hide()

        self.money = CountLabel(style.format_money)
        self.money.setFont(style.title_font(24))
        self.happiness = CountLabel(lambda v: f"{v:,}")
        self.happiness.setFont(style.title_font(22))
        self.score = QLabel("")
        self.score.setFont(style.title_font(13))
        self.score.setStyleSheet(f"color: {style.TEXT_QUIET};")
        self.stat_bars = {name: StatBar(name) for name in STAT_NAMES}
        self.income = QLabel("")
        self.income.setStyleSheet(f"color: {style.TEXT_QUIET}; font-size: 11px;")
        self.income.setWordWrap(True)
        self.items = QLabel("")
        self.items.setStyleSheet(f"background: #FFF1C2; color: #7A5600; border: 2px solid {style.INK};"
                                 " border-radius: 9px; padding: 1px 8px; font-size: 11px; font-weight: bold;")
        self.items.hide()

        name_row = QHBoxLayout()
        name_row.setSpacing(6)
        name_row.addWidget(self.name)
        name_row.addWidget(self.npc_chip)
        name_row.addWidget(self.character)
        name_row.addStretch(1)
        name_row.addWidget(self.turn_tag)
        chips = QHBoxLayout()
        chips.setSpacing(5)
        chips.addWidget(self.chip_job)
        chips.addWidget(self.chip_stage)
        chips.addStretch(1)
        who = QVBoxLayout()
        who.setSpacing(2)
        who.addLayout(name_row)
        who.addLayout(chips)
        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(self.face, 0, Qt.AlignTop)
        top.addLayout(who, 1)
        top.addWidget(self.medal, 0, Qt.AlignTop)

        money_row = QHBoxLayout()
        money_row.setSpacing(5)
        money_row.addWidget(IconWidget("coin", 22))
        money_row.addWidget(self.money)
        money_row.addSpacing(10)
        money_row.addWidget(IconWidget("heart", 20))
        money_row.addWidget(self.happiness)
        money_row.addStretch(1)
        money_row.addWidget(self.score, 0, Qt.AlignBottom)

        stats = QHBoxLayout()
        stats.setSpacing(8)
        for bar in self.stat_bars.values():
            stats.addWidget(bar, 1)

        foot = QHBoxLayout()
        foot.addWidget(self.income, 1)
        foot.addWidget(self.items, 0, Qt.AlignRight)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)
        layout.addLayout(top)
        layout.addLayout(money_row)
        layout.addLayout(stats)
        layout.addLayout(foot)
        self.set_current(False)

    def update_info(self, info: PlayerInfo, rank: int) -> None:
        self.face.set_face(info.character, self.color_hex, info.is_npc)
        self.name.setText(info.name)
        self.npc_chip.setVisible(info.is_npc)
        self.character.setText(info.character)
        job = info.job or ("의대생" if info.job_state == "student" else "직업 없음")
        set_chip(self.chip_job, job, *JOB_CHIP, bold=True)
        set_chip(self.chip_stage, "인생 완주!" if info.finished else stage_text(info), *STAGE_CHIP, bold=True)
        self.money.set_value(info.money)
        self.money.setStyleSheet(f"color: {style.BAD if info.money < 0 else style.INK};")   # 빚은 빨강
        self.money.setToolTip("빚" if info.money < 0 else "")
        self.happiness.set_value(info.happiness)
        self.score.setText(f"총점 {info.score:,}")
        for name, bar in self.stat_bars.items():
            bar.set_value(info.stats.get(name, 0))
        self.medal.set_rank(rank)
        self.income.setText(income_text(info))
        extras = list(info.items)
        if info.insurance:
            extras.append("보험")
        if info.lecture_pass:
            extras.append("인강 패스")
        self.items.setText(", ".join(extras))
        self.items.setVisible(bool(extras))

    def set_current(self, current: bool) -> None:
        self.current = current
        if current:
            bg = style.mix("#FFFFFF", self.color_hex, 0.1).name()
            set_card_border(self, self.color_hex, 4, bg, 18)
        else:
            set_card_border(self, style.INK, 3, style.CARD_BG, 18)
        self.turn_tag.setVisible(current)
        effect = self.graphicsEffect()
        if effect is not None:
            effect.setOffset(0, 8 if current else 4)


class PanelView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setStyleSheet("QWidget#panel { background: transparent; }")
        self.cards: dict = {}

        self.round_label = QLabel("1라운드")
        self.round_label.setFont(style.title_font(18))
        self.round_label.setStyleSheet(f"background: white; border: 3px solid {style.INK}; border-radius: 14px;"
                                       " padding: 2px 14px;")
        sticker_shadow(self.round_label, 3)
        self.trend_label = QLabel("")
        self.trend_label.setFont(style.title_font(14))
        self.trend_label.setStyleSheet(f"background: {style.SUN}; border: 3px solid {style.INK}; border-radius: 14px;"
                                       " padding: 3px 12px;")
        sticker_shadow(self.trend_label, 3)
        self.trend_label.hide()
        self.turn_label = QLabel("게임 준비 중")      # 예전 이름 호환 (화면에는 배너가 대신 보여 준다)
        self.turn_label.hide()

        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(self.round_label)
        head.addWidget(self.trend_label, 1)

        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(14)

        self.note = QLabel("총점 = 돈(만원) + 행복 × 10. 노년기를 마치면 총점으로 순위를 정해요.")
        self.note.setWordWrap(True)
        self.note.setStyleSheet(f"color: {style.INK}; font-size: 11px; background: rgba(255,255,255,150);"
                                " border-radius: 8px; padding: 4px 8px;")
        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumBlockCount(300)
        self.log_box.setFixedHeight(110)
        self.log_box.setPlaceholderText("진행 기록이 여기에 쌓여요")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 10, 10)
        layout.setSpacing(12)
        layout.addLayout(head)
        layout.addLayout(self.cards_layout)
        layout.addWidget(self.note)
        layout.addStretch(1)
        layout.addWidget(self.log_box)

    def set_players(self, players) -> None:
        """게임 시작 시 플레이어 수만큼 카드를 만든다."""
        for card in self.cards.values():
            card.setParent(None)
        self.cards.clear()
        for order, p in enumerate(players):
            info = read_player(p)
            card = PlayerCard(order + 1, style.player_color_hex(order))
            self.cards_layout.addWidget(card)
            self.cards[info.id] = card
        self.update_players(players)

    def update_players(self, players) -> None:
        """수치가 바뀔 때마다 Model 값으로 카드 내용을 덮어쓴다. 돈·행복은 세면서 바뀐다."""
        infos = [read_player(p) for p in players]
        ranks = rank_of(infos)
        for info in infos:
            card = self.cards.get(info.id)
            if card is not None:
                card.update_info(info, ranks[info.id])

    def set_current_player(self, player) -> None:
        info = read_player(player)
        for pid, card in self.cards.items():
            card.set_current(pid == info.id)
        who = f"{info.name} (NPC)" if info.is_npc else info.name
        self.turn_label.setText(f"현재 차례: {who}")

    def set_round(self, number: int) -> None:
        self.round_label.setText(f"{number}라운드")

    def set_trend(self, text: str) -> None:
        self.trend_label.setText(text)
        self.trend_label.setVisible(bool(text))

    def add_log(self, text: str) -> None:
        self.log_box.appendPlainText(text)


def rank_of(infos) -> dict:
    """총점 순위 (같으면 돈이 많은 쪽이 앞). player_id → 1, 2, 3 …"""
    ordered = sorted(infos, key=lambda i: (i.score, i.money), reverse=True)
    return {info.id: n for n, info in enumerate(ordered, start=1)}
