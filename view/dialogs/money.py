"""
view/dialogs/money.py  —  돈을 쓰는 창

  ShopDialog     상점 (돈이 모자란 상품은 비활성화)                       FR-01-20
  InvestDialog   투자 시간! 회사 고르기 + 금액(슬라이더·스핀박스·10/30/50%)  FR-01-16, FR-01-19, FR-02-11
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QLabel, QLineEdit, QSlider, QSpinBox, QGridLayout, QHBoxLayout,
                             QVBoxLayout, QMessageBox, QFrame)

from common.adapter import read_item, read_company, CompanyInfo
from view import style
from view.widgets import title, quiet, button, card_frame, chip, hbox, set_card_border
from view.dialogs.base import BaseDialog, effect_html


# ════════════════════════════════════════════════════════════════
# 상점
# ════════════════════════════════════════════════════════════════
class ShopDialog(BaseDialog):
    """상점: 상품 카드 목록, 돈이 모자라면 비활성화. 고른 상품 번호, 안 사면 None"""

    def __init__(self, player_name: str, money: int, items, parent=None):
        super().__init__(parent, 640, "상점")
        self.selected_index = None

        grid = QGridLayout()
        grid.setSpacing(10)
        for i, raw in enumerate(items):
            item = read_item(raw)
            ok = item.price <= money
            card = card_frame(f"item{i}", border=style.CARD_LINE if ok else "#EEE6D9", bg="white" if ok else "#FAF7F2")
            box = QVBoxLayout(card)
            box.setContentsMargins(12, 10, 12, 10)
            box.addWidget(title(item.name, 18))
            box.addWidget(QLabel(f"가격 <b>{style.format_money(item.price)}</b>"))
            effect = item.description or effect_html(item.money, item.happiness, item.stats)
            label = QLabel(effect)
            label.setWordWrap(True)
            box.addWidget(label)
            buy = button("사기" if ok else "돈이 모자라요", role="primary" if ok else "", min_height=32)
            buy.setEnabled(ok)
            buy.clicked.connect(lambda _, idx=i: self._choose(idx))
            box.addWidget(buy)
            grid.addWidget(card, i // 3, i % 3)

        leave = button("그냥 나갈래요")
        leave.clicked.connect(self.reject)
        self.body.addLayout(hbox(title(f"{player_name}님, 상점에 왔어요!", 24), "stretch",
                                 chip(f"보유 {style.format_money(money)}", "#FFF4C7", "#8A6A00", bold=True, size=13)))
        self.body.addWidget(quiet("한 번에 하나만 살 수 있어요."))
        self.body.addLayout(grid)
        self.body.addWidget(leave, 0, Qt.AlignRight)

    def _choose(self, index: int) -> None:
        self.selected_index = index
        self.accept()


# ════════════════════════════════════════════════════════════════
# 투자
# ════════════════════════════════════════════════════════════════
def risk_drops(company: CompanyInfo) -> str:
    level = {"stable": 1, "growth": 2, "gamble": 3}.get(company.type, 2)
    return "위험도 " + "●" * level + "○" * (3 - level)


class InvestDialog(BaseDialog):
    """투자 화면 (상세 설계 14장 그림 5). '투자하기!'를 누르면 Input의 검사 함수로 확인하고 통과해야 닫힌다.
    결과: company_id, amount (만원) / 건너뛰면 reject"""

    def __init__(self, player_name: str, money: int, companies, validator, parent=None):
        super().__init__(parent, 880, "투자")
        self.validator = validator         # (company_id, amount) → 오류 메시지("" = 통과)
        self.money = max(0, money)
        self.companies = [read_company(c) for c in companies]
        self.company_id = None
        self.cards = {}

        head = QHBoxLayout()
        head_col = QVBoxLayout()
        head_col.addWidget(title("투자 시간!", 30))
        head_col.addWidget(quiet(f"{player_name}님, 5턴 뒤에 주사위로 결과가 나와요"))
        head.addLayout(head_col)
        head.addStretch(1)
        head.addWidget(chip(f"보유 {style.format_money(money)}", "#FFF1C2", "#7A5600", bold=True, size=15))
        self.body.addLayout(head)

        grid = QGridLayout()
        grid.setSpacing(10)
        for i, c in enumerate(self.companies):
            grid.addWidget(self._card(i, c), 0, i)
        self.body.addLayout(grid)

        # 금액 입력: 슬라이더 + 스핀박스 + 10/30/50% (FR-02-11)
        amount_box = card_frame("amountbox")
        amount = QVBoxLayout(amount_box)
        amount.setContentsMargins(16, 10, 16, 10)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, self.money)
        self.spin = QSpinBox()
        self.spin.setRange(0, max(0, self.money))
        self.spin.setSuffix(" 만원")
        self.spin.setGroupSeparatorShown(True)
        self.spin.setMinimumWidth(140)
        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)
        self.spin.valueChanged.connect(lambda _: self._update_summary())
        percent_buttons = []
        for pct in (10, 30, 50):
            b = button(f"{pct}%", min_height=30)
            b.clicked.connect(lambda _, x=pct: self.spin.setValue(self.money * x // 100))
            percent_buttons.append(b)
        amount.addLayout(hbox(title("얼마나 넣을까요?", 18), "stretch", *percent_buttons, self.spin))
        amount.addWidget(self.slider)
        self.summary = QLabel("")
        self.summary.setWordWrap(True)
        amount.addWidget(self.summary)
        self.body.addWidget(amount_box)

        skip = button("이번엔 건너뛰기")
        skip.clicked.connect(self.reject)
        self.invest_button = button("투자하기!", role="good", min_height=46)
        self.invest_button.setDefault(True)
        self.invest_button.clicked.connect(self.accept)
        self.body.addLayout(hbox("stretch", skip, self.invest_button))

        if self.companies:
            self._select(self.companies[0].id)
        self.spin.setValue(self.money * 30 // 100)

    def _card(self, i: int, c: CompanyInfo):
        card = card_frame(f"co{i}")
        card.setCursor(Qt.PointingHandCursor)
        box = QVBoxLayout(card)
        box.setContentsMargins(12, 10, 12, 10)
        box.setSpacing(3)
        color = style.COMPANY_TYPE_COLORS.get(c.type, style.POOL)
        box.addLayout(hbox(chip(c.type_name, color, "white", bold=True), "stretch"))
        box.addWidget(title(c.name, 20))
        box.addWidget(QLabel(f"<span style='color:{style.BAD}'>{risk_drops(c)}</span>"))
        box.addWidget(title(f"기대 {style.format_ratio_x100(c.expected_x100)}", 20, style.GOOD))
        if c.ratios_x10:
            box.addWidget(quiet(f"최악 {style.format_ratio_x10(min(c.ratios_x10))}, 최고 {style.format_ratio_x10(max(c.ratios_x10))}", 11))
        pick_button = button("이 회사 고르기", min_height=30)
        pick_button.clicked.connect(lambda _, cid=c.id: self._select(cid))
        box.addWidget(pick_button)
        card.mousePressEvent = lambda _e, cid=c.id: self._select(cid)
        self.cards[c.id] = card
        return card

    def _select(self, company_id) -> None:
        self.company_id = company_id
        for cid, card in self.cards.items():
            if cid == company_id:
                set_card_border(card, style.INK, 4, "#FFF6D6")
            else:
                set_card_border(card, style.CARD_LINE, 3)
        self._update_summary()

    def selected_company(self):
        return next((c for c in self.companies if c.id == self.company_id), None)

    def amount(self) -> int:
        return self.spin.value()

    def _update_summary(self) -> None:
        c = self.selected_company()
        amount = self.amount()
        if c is None or amount <= 0:
            self.summary.setText("회사를 고르고 금액을 정하세요.")
            return
        expected = amount * c.expected_x100 // 100
        text = (f"<b>{style.format_money(amount)}</b>을 {c.name}에 넣으면 5턴 뒤 기대 "
                f"<span style='color:{style.GOOD}'><b>약 {style.format_money(expected)}</b></span>")
        self.summary.setText(text)

    def accept(self) -> None:
        message = self.validator(self.company_id, self.amount()) if self.validator else ""
        if message:
            QMessageBox.warning(self, "입력 확인", message)
            return
        super().accept()
