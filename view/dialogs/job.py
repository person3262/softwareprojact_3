"""
view/dialogs/job.py  —  직업과 직업별 고유 장치 창

  JobDialog       직업 선택 (조건 미달 직업 비활성화)                 FR-01-12, FR-02-08
  ExamDialog      의사 국가고시 (보기 4개, 키보드 1~4, 남은 시간 막대) FR-01-24, FR-02-14
  BusinessDialog  사업가 업종 고르기·바꾸기 (유행 표시)                FR-01-26, FR-02-15
  GigDialog       프리랜서 의뢰 게시판 (카드 3장 + 쉬기)              FR-01-27, FR-02-16
  ArtworkDialog   예술가 작품 완성 (팔기·보관, 작업실 2칸)             FR-01-28, FR-02-17

창은 고른 값만 돌려준다. 값의 검사는 Input이 넣어 주는 validator가 하고, 규칙 계산은 Model이 한다.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (QLabel, QGridLayout, QHBoxLayout, QVBoxLayout, QMessageBox, QPushButton)

from common.constants import STAT_NAMES, BUSINESS_TIERS, STUDIO_SIZE
from common.adapter import (read_job, read_question, read_business, read_gig, read_artwork,
                            meets_requirements, pick)
from view import style
from view.widgets import title, quiet, button, card_frame, chip, Bar, hbox
from view.dialogs.base import BaseDialog, big_label, stats_text, effect_html

MSG_STUDIO_FULL = "작업실이 꽉 찼습니다. 팔 작품을 고르세요."
MSG_TIME_OVER = "시간 초과! 내년을 기약하자..."
CATEGORY_COLORS = {"돈 우선": ("#FDE7E7", "#C0392B"), "밸런스": ("#E3EEFC", "#2D5FA8"),
                   "행복 우선": ("#FDE7F1", "#B0306A")}


def dice_chance(low: int, high: int) -> int:
    """주사위 2개 합이 low~high일 확률(%) — 정수로 반올림"""
    ways = sum(1 for a in range(1, 7) for b in range(1, 7) if low <= a + b <= high)
    return (ways * 100 + 18) // 36


# ════════════════════════════════════════════════════════════════
# 직업 선택
# ════════════════════════════════════════════════════════════════
class JobDialog(BaseDialog):
    """직업 목록·조건·칸당 수입 표시, 조건이 안 되는 직업은 비활성화.
    exclude: 고를 수 없는 직업 id (국가고시 포기 후 의사 등) / allow_keep: '지금 직업 유지' 버튼"""

    def __init__(self, player_name: str, jobs, stats: dict, exclude=(), allow_keep: bool = False,
                 heading: str = "", parent=None):
        super().__init__(parent, 960, "직업 선택")
        self.selected_id = None
        self.kept = False

        grid = QGridLayout()
        grid.setSpacing(10)
        any_ok = False
        for i, raw in enumerate(jobs):
            job = read_job(raw)
            ok = meets_requirements(stats, job.requirements) and job.id not in exclude
            any_ok = any_ok or ok
            grid.addWidget(self._job_card(i, job, stats, ok, job.id in exclude), i // 3, i % 3)

        self.body.addWidget(title(heading or f"{player_name}님, 성년기 진입! 직업을 고르세요", 24))
        self.body.addWidget(quiet(f"내 능력치: {stats_text(stats)}  ·  조건이 안 되는 직업은 고를 수 없어요."))
        self.body.addLayout(grid)
        if allow_keep:
            keep = button("지금 직업 유지")
            keep.clicked.connect(self._keep)
            self.body.addWidget(keep, 0, Qt.AlignRight)
        if not any_ok and not allow_keep:
            self.body.addWidget(QLabel("선택할 수 있는 직업이 없습니다."))
            close = button("확인")
            close.clicked.connect(self.reject)
            self.body.addWidget(close)

    def _job_card(self, i: int, job, stats: dict, ok: bool, excluded: bool):
        card = card_frame(f"job{i}", border=style.CARD_LINE if ok else "#EEE6D9",
                          bg="white" if ok else "#FAF7F2")
        box = QVBoxLayout(card)
        box.setContentsMargins(12, 10, 12, 10)
        box.setSpacing(4)
        name_row = QHBoxLayout()
        name_row.addWidget(title(job.name, 20, style.INK if ok else style.TEXT_QUIET))
        name_row.addStretch(1)
        if job.category:
            name_row.addWidget(chip(job.category, *CATEGORY_COLORS.get(job.category, ("#EEF1F6", "#4A4F63"))))
        box.addLayout(name_row)

        # 조건은 한 줄에 하나씩 (줄바꿈이 자동으로 생기면 글자가 겹치는 일이 있어서 직접 나눈다)
        if job.requirements:
            parts = []
            for stat, need in job.requirements.items():
                have = stats.get(stat, 0)
                color = style.GOOD if have >= need else style.BAD
                parts.append(f"<span style='color:{color}'>{stat} {need} 이상 (지금 {have})</span>")
            need_label = QLabel("조건: " + "<br>".join(parts))
        else:
            need_label = QLabel("조건 없음 — 누구나")
        need_label.setStyleSheet("font-size: 12px;")
        box.addWidget(need_label)

        if job.device == "business":
            income = "매 턴: 업종 실적표 (주사위 합)"
        else:
            income = f"매 턴 칸당: 돈 {style.format_money(job.income_money)} · 행복 {job.income_happiness}"
        income_label = QLabel(f"{income}<br><span style='font-weight:normal'>노년기 연금 {job.pension}%</span>")
        income_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        box.addWidget(income_label)
        if job.description:
            desc = quiet(job.description, 11)
            desc.setWordWrap(True)
            desc.setMinimumHeight(desc.fontMetrics().lineSpacing() * 2 + 4)   # 두 줄 자리를 미리 잡는다
            box.addWidget(desc)
        box.addStretch(1)
        pick_button = button("이 직업으로!" if ok else ("이번엔 못 골라요" if excluded else "조건 부족"),
                             role="primary" if ok else "", min_height=34)
        pick_button.setEnabled(ok)
        pick_button.clicked.connect(lambda _, jid=job.id: self._choose(jid))
        box.addWidget(pick_button)
        return card

    def _choose(self, jid) -> None:
        self.selected_id = jid
        self.accept()

    def _keep(self) -> None:
        self.kept = True
        self.selected_id = None
        self.accept()


# ════════════════════════════════════════════════════════════════
# 의사 국가고시
# ════════════════════════════════════════════════════════════════
class ExamDialog(BaseDialog):
    """국가고시 문제 하나. 보기 버튼·키보드 1~4로 답하고, 처음 누른 답만 인정한다.
    시간이 다 되면 answer = None (오답).
    npc_answer가 주어지면 'NPC가 고민 중...'을 보여 준 뒤 그 답을 고르고 닫힌다."""

    TICK_MS = 1000          # 남은 시간이 줄어드는 간격 (테스트에서는 짧게 바꾼다)

    def __init__(self, player_name: str, question, level: int, level_name: str, time_limit: int,
                 npc_answer=None, npc_delay_ms: int = 1000, parent=None):
        super().__init__(parent, 560, "국가고시")
        q = read_question(question)
        self.answer = None
        self.timed_out = False
        self.time_limit = max(1, int(time_limit))
        self.left = self.time_limit
        self._answered = False

        head = hbox(chip(f"국가고시 · {level}단계 {level_name}", "#E8F7F5", "#1F8A7E", bold=True, size=12),
                    "stretch", chip(player_name, "#EEF1F6", "#4A4F63"))
        self.body.addLayout(head)
        self.body.addWidget(big_label(q.question, 24))

        self.choice_buttons = []
        for n, text in enumerate(q.choices, start=1):
            b = QPushButton(f"{n}.  {text}")
            b.setMinimumHeight(44)
            b.setStyleSheet("text-align: left; padding-left: 16px; font-size: 15px;")
            b.clicked.connect(lambda _, k=n: self._choose(k))
            self.body.addWidget(b)
            self.choice_buttons.append(b)

        self.time_bar = Bar("#2BB3A3", self.time_limit, 12)
        self.time_bar.set_value(self.left)
        self.time_label = QLabel(f"남은 시간 {self.left}초")
        self.time_label.setFont(style.title_font(16))
        self.body.addLayout(hbox(self.time_bar, self.time_label, spacing=10))

        self.status = quiet("보기를 누르거나 키보드 1~4를 누르세요. 처음 누른 답만 인정돼요.")
        self.body.addWidget(self.status)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        if npc_answer is None:
            self._timer.start(self.TICK_MS)
        else:                                   # NPC: 고민하는 척 → 답 표시 → 닫기
            for b in self.choice_buttons:
                b.setEnabled(False)
            self.status.setText(f"{player_name}(NPC)가 고민 중...")
            QTimer.singleShot(npc_delay_ms, lambda: self._show_npc(npc_answer))

    def keyPressEvent(self, event) -> None:
        key = event.text()
        if key in ("1", "2", "3", "4") and self.choice_buttons and self.choice_buttons[0].isEnabled():
            self._choose(int(key))
            return
        if event.key() == Qt.Key_Escape:        # 시험 중에는 Esc로 닫지 않는다
            return
        super().keyPressEvent(event)

    def _choose(self, n: int) -> None:
        if self._answered:                      # 12.2 예외: 여러 번 눌러도 첫 입력만 인정
            return
        self._answered = True
        self.answer = n
        self._timer.stop()
        self._mark(n)
        QTimer.singleShot(250, self.accept)

    def _mark(self, n: int) -> None:
        for k, b in enumerate(self.choice_buttons, start=1):
            b.setEnabled(False)
            if k == n:
                b.setStyleSheet(f"text-align: left; padding-left: 16px; font-size: 15px; background: {style.ACCENT};"
                                f" color: {style.INK}; border: 3px solid {style.INK}; border-radius: 12px;")

    def _tick(self) -> None:
        self.left -= 1
        self.time_bar.set_value(self.left)
        self.time_label.setText(f"남은 시간 {max(0, self.left)}초")
        if self.left <= 3:
            self.time_label.setStyleSheet(f"color: {style.BAD};")
        if self.left <= 0 and not self._answered:
            self._answered = True
            self.timed_out = True
            self._timer.stop()
            for b in self.choice_buttons:
                b.setEnabled(False)
            self.status.setText(MSG_TIME_OVER)
            QTimer.singleShot(400, self.accept)

    def _show_npc(self, n: int) -> None:
        self.answer = n
        self._answered = True
        self._mark(n)
        self.status.setText(f"{n}번을 골랐다!")
        QTimer.singleShot(600, self.accept)


# ════════════════════════════════════════════════════════════════
# 사업가 업종
# ════════════════════════════════════════════════════════════════
def short_money(n: int) -> str:
    """업종 카드처럼 좁은 칸용: 700 → '+700만원', 0 → '0원'"""
    return style.format_money_delta(n)


def trend_modifier(business, trend) -> int:
    """화면 표시용 유행 보정값: 유행 업종이면 +trend_bonus, 아니면 off_trend (NFT만 -1)"""
    return business.trend_bonus if trend == business.id else business.off_trend


class BusinessDialog(BaseDialog):
    """사업가 업종 고르기 / 바꾸기 (상세 설계 4.1, FR-02-15)

    고르기 모드(current=None) : 업종 3개 중 하나를 고른다.
    바꾸기 모드(current=업종 id) : 다른 업종으로 바꾸거나 '그대로 하기'. 지금 업종과 비용이 모자란 업종은 비활성화.
    """

    def __init__(self, player_name: str, businesses, trend=None, rounds_left: int = 0,
                 current=None, money: int = 0, cost: int = 0, validator=None, parent=None):
        super().__init__(parent, 760, "업종 바꾸기" if current is not None else "업종 선택")
        self.switch_mode = current is not None
        self.validator = validator          # 업종 id → 오류 메시지("" = 통과). Input이 넣어 준다.
        self.selected_id = None
        infos = [read_business(b) for b in businesses]
        names = {b.id: b.name for b in infos}

        trend_text = names.get(trend, "유행 없음") if trend else "유행 없음"
        trend_label = QLabel(f"지금 유행: <b>{trend_text}</b> ({rounds_left}라운드 남음)")
        trend_label.setStyleSheet("background: #FFE8D6; border-radius: 10px; padding: 6px 12px;")

        grid = QGridLayout()
        grid.setSpacing(10)
        for col, b in enumerate(infos):
            grid.addWidget(self._card(col, b, trend, current, money, cost), 0, col)

        if self.switch_mode:
            self.body.addWidget(title(f"{player_name}님, 출발 칸! 업종을 바꿀까요?", 24))
            self.body.addWidget(quiet(f"지금 업종: {names.get(current, current)} · 보유 자금: {style.format_money(money)}"
                                      f" · 바꾸는 비용: {style.format_money(cost)}"))
        else:
            self.body.addWidget(title(f"{player_name}님, 어떤 사업을 할까요?", 24))
            self.body.addWidget(quiet("매 턴 주사위 합으로 실적이 정해져요. 유행하는 업종은 주사위 합이 올라가요."))
        self.body.addWidget(trend_label)
        self.body.addLayout(grid)
        if self.switch_mode:
            keep = button("그대로 하기")
            keep.setDefault(True)
            keep.clicked.connect(self.reject)
            self.body.addWidget(keep, 0, Qt.AlignRight)

    def _card(self, col: int, b, trend, current, money: int, cost: int):
        hot = trend == b.id
        card = card_frame(f"biz{col}", border="#F2994A" if hot else style.CARD_LINE, width=3 if hot else 2)
        box = QVBoxLayout(card)
        box.setContentsMargins(12, 10, 12, 10)
        box.setSpacing(4)
        box.addWidget(title(b.name + ("  (유행 중!)" if hot else ""), 18))
        box.addWidget(quiet(f"{b.kind} · {b.desc}", 11))

        table = QGridLayout()
        table.setVerticalSpacing(2)
        for row, tier in enumerate(BUSINESS_TIERS):
            m, h = b.table[row] if row < len(b.table) else (0, 0)
            table.addWidget(QLabel(tier), row, 0)
            money_label = QLabel(short_money(m))
            money_label.setStyleSheet(f"color: {style.delta_color(m)}; font-weight: bold;")
            table.addWidget(money_label, row, 1)
            table.addWidget(QLabel(f"행복 {style.format_delta(h)}" if h else ""), row, 2)
        box.addLayout(table)

        bonus = trend_modifier(b, trend)
        if bonus > 0:
            note = f"지금 보정: 주사위 합 +{bonus}"
        elif bonus < 0:
            note = f"지금 보정: 주사위 합 {bonus} (거품 빠짐)"
        else:
            note = f"유행이면 주사위 합 +{b.trend_bonus}"
        note_label = QLabel(note)
        note_label.setStyleSheet(f"color: {style.delta_color(bonus) if bonus else style.TEXT_QUIET}; font-size: 12px;")
        box.addWidget(note_label)

        if not self.switch_mode:
            pick_button = button("이 업종 선택", role="primary", min_height=34)
        elif b.id == current:
            pick_button = button("지금 업종", min_height=34)
            pick_button.setEnabled(False)
        elif money < cost:              # 12장 예외: 비용 부족 → 버튼 비활성화
            pick_button = button("비용 부족", min_height=34)
            pick_button.setEnabled(False)
        else:
            pick_button = button(f"바꾸기 (-{style.format_money(cost)})", role="primary", min_height=34)
        pick_button.clicked.connect(lambda _, bid=b.id: self._choose(bid))
        box.addWidget(pick_button)
        return card

    def _choose(self, business_id) -> None:
        message = self.validator(business_id) if self.validator else ""
        if message:                     # 버튼이 막혀 있어도 한 번 더 검사 (이중 방어)
            QMessageBox.warning(self, "입력 확인", message)
            return
        self.selected_id = business_id
        self.accept()


# ════════════════════════════════════════════════════════════════
# 프리랜서 의뢰 게시판
# ════════════════════════════════════════════════════════════════
def gig_outcome_text(g) -> str:
    """'2~8 (72%): 잔금 받기 전에 잠수. 돈 -700만원' 같은 설명"""
    parts = []
    if g.risk:
        low, high = g.risk
        acc = g.accident
        effect = effect_text(acc.get("money", 0), acc.get("happiness", 0))
        parts.append(f"사고 {low}~{high} ({dice_chance(low, high)}%): {acc.get('text', '')}. {effect}")
    if g.jackpot:
        low, high = g.jackpot
        bonus = g.bonus
        effect = "다음 의뢰 보수 2배" if bonus.get("double_next") else effect_text(bonus.get("money", 0), 0)
        parts.append(f"대박 {low}~{high} ({dice_chance(low, high)}%): {bonus.get('text', '')}! {effect}")
    return "\n".join(parts) if parts else "사고 없음"


def effect_text(money: int, happiness: int) -> str:
    items = []
    if money:
        items.append(f"돈 {style.format_money_delta(money)}")
    if happiness:
        items.append(f"행복 {style.format_delta(happiness)}")
    return ", ".join(items)


class GigDialog(BaseDialog):
    """의뢰 카드 3장 중 하나를 맡거나 '이번 바퀴는 쉰다'. 고른 카드 id, 쉬면 None"""

    def __init__(self, player_name: str, cards, stats: dict, rest_happiness: int = 50, parent=None):
        super().__init__(parent, 820, "의뢰 게시판")
        self.selected_id = None
        self.rested = False

        grid = QGridLayout()
        grid.setSpacing(10)
        for col, raw in enumerate(cards):
            grid.addWidget(self._card(col, read_gig(raw), stats), 0, col)

        rest = button(f"이번 바퀴는 쉰다 (안식월, 행복 +{rest_happiness})")
        rest.clicked.connect(self._rest)
        self.body.addWidget(title(f"{player_name}님, 의뢰 게시판이 새로 붙었어요", 24))
        self.body.addWidget(quiet("맡은 의뢰는 다음에 출발 칸을 지날 때 정산해요. 보수를 받고, 정산 주사위로 사고·대박이 정해져요."))
        self.body.addLayout(grid)
        self.body.addWidget(rest, 0, Qt.AlignRight)

    def _card(self, col: int, g, stats: dict):
        card = card_frame(f"gig{col}")
        box = QVBoxLayout(card)
        box.setContentsMargins(12, 10, 12, 10)
        box.setSpacing(5)
        head = QHBoxLayout()
        head.addWidget(title(g.name, 18))
        head.addStretch(1)
        risk = "대박형" if not g.stars else "위험도 " + "★" * g.stars
        head.addWidget(chip(risk, "#FDE5E5" if g.stars >= 3 else "#EEF1F6", "#C0392B" if g.stars >= 3 else "#4A4F63"))
        box.addLayout(head)
        quote = QLabel(f"“{g.quote}”")
        quote.setWordWrap(True)
        quote.setStyleSheet(f"color: {style.TEXT_QUIET}; font-style: italic; font-size: 12px;")
        box.addWidget(quote)
        pay = QLabel(f"보수 {effect_html(g.pay, g.happiness, g.stats)}")
        pay.setStyleSheet("font-size: 13px;")
        box.addWidget(pay)
        outcome = QLabel(gig_outcome_text(g))
        outcome.setWordWrap(True)
        outcome.setStyleSheet("font-size: 11px;")
        box.addWidget(outcome)
        if g.stat:
            box.addWidget(chip(f"피해 감소: {g.stat} {stats.get(g.stat, 0)}", "#E3EEFC", "#2D5FA8"))
        box.addStretch(1)
        take = button("이 의뢰 맡기", role="primary", min_height=34)
        take.clicked.connect(lambda _, gid=g.id: self._choose(gid))
        box.addWidget(take)
        return card

    def _choose(self, gid) -> None:
        self.selected_id = gid
        self.accept()

    def _rest(self) -> None:
        self.rested = True
        self.selected_id = None
        self.accept()


# ════════════════════════════════════════════════════════════════
# 예술가 작품
# ════════════════════════════════════════════════════════════════
GRADE_COLORS = {"망작": ("#EEF1F6", "#4A4F63"), "습작": ("#E3EEFC", "#2D5FA8"),
                "수작": ("#E4F6EA", "#1E7A45"), "명작": ("#FFF4C7", "#8A6A00")}


class ArtworkDialog(BaseDialog):
    """작품 완성 창. 돌려주는 값 = 팔 작품 id, 모두 보관하면 None.
    작업실이 꽉 차 있으면 3점 중 하나를 골라 팔기 전에는 닫히지 않는다. (12.2 예외)"""

    def __init__(self, player_name: str, artwork, studio, studio_size: int = STUDIO_SIZE, parent=None):
        super().__init__(parent, 640, "작품 완성")
        new = read_artwork(artwork)
        kept = [read_artwork(a) for a in (studio or [])]
        self.sell_id = None
        self.must_sell = len(kept) >= studio_size
        self.new_id = new.id

        self.body.addWidget(title(f"{player_name}님의 새 작품 완성!", 24))
        self.body.addWidget(self._work_card("new", new, pick(artwork, ("text",), ""), big=True))

        self.body.addWidget(title(f"작업실 ({len(kept)}/{studio_size})", 18))
        slots = QHBoxLayout()
        slots.setSpacing(10)
        for i in range(studio_size):
            if i < len(kept):
                slots.addWidget(self._work_card(f"slot{i}", kept[i]))
            else:
                empty = card_frame(f"empty{i}", border="#E6DCCB", bg="#FAF7F2")
                QVBoxLayout(empty).addWidget(quiet("빈 칸", 12), 0, Qt.AlignCenter)
                empty.setMinimumHeight(70)
                slots.addWidget(empty)
        self.body.addLayout(slots)

        if self.must_sell:
            warn = QLabel(MSG_STUDIO_FULL)
            warn.setStyleSheet(f"color: {style.BAD}; font-weight: bold;")
            self.body.addWidget(warn)
        else:
            sell = button(f"바로 팔기 (+{style.format_money(new.price)})")
            sell.clicked.connect(lambda: self._sell(new.id))
            keep = button("작업실에 보관", role="primary")
            keep.setDefault(True)
            keep.clicked.connect(self.accept)
            self.body.addLayout(hbox(sell, keep))
        self.body.addWidget(quiet("노년기에 들어설 때 회고전에서 보관 작품을 판매가의 2배에 팔아요."))

    def _work_card(self, name: str, work, text: str = "", big: bool = False):
        card = card_frame(name, border=style.INK if big else style.CARD_LINE, width=3 if big else 2)
        box = QVBoxLayout(card)
        box.setContentsMargins(12, 8, 12, 8)
        box.setSpacing(3)
        row = QHBoxLayout()
        row.addWidget(title(f"‘{work.title}’", 22 if big else 15))
        row.addStretch(1)
        row.addWidget(chip(work.grade or "?", *GRADE_COLORS.get(work.grade, ("#EEF1F6", "#4A4F63")), bold=True))
        box.addLayout(row)
        box.addWidget(QLabel(f"판매가 {style.format_money(work.price)}  ·  회고전 {style.format_money(work.price * 2)}"))
        if text:
            box.addWidget(quiet(text, 12))
        if self.must_sell:
            sell = button("이 작품 팔기", role="primary", min_height=30)
            sell.clicked.connect(lambda _, wid=work.id: self._sell(wid))
            box.addWidget(sell)
        return card

    def _sell(self, work_id) -> None:
        self.sell_id = work_id
        super().accept()

    def accept(self) -> None:
        if self.must_sell and self.sell_id is None:
            QMessageBox.warning(self, "작업실", MSG_STUDIO_FULL)
            return
        super().accept()

    def reject(self) -> None:
        if self.must_sell:                    # 꽉 찼을 때는 팔 작품을 고르기 전에는 닫히지 않는다
            QMessageBox.warning(self, "작업실", MSG_STUDIO_FULL)
            return
        super().reject()                      # Esc = 보관
