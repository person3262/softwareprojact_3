"""
view/popup_view.py  —  PopupView: 알림창과 선택창 (FR-02-06 ~ FR-02-09)

PopupView는 "어떤 창을 띄울지" 고르는 창구 역할이고, 실제 창은 아래 Dialog 클래스들이다.

  묻는 창 (ask_*) : 사용자가 고른 값을 돌려준다. 값의 검사·변환은 Input이 한다.
    SetupDialog      게임 설정 (플레이어 수, 이름, NPC 지정)        FR-03-01, FR-03-03
    CharacterDialog  캐릭터 선택 (능력치·특성 표시, 중복 선택 불가) FR-01-08, FR-02-07
    JobDialog        직업 선택 (조건 미달 직업 비활성화)            FR-01-12, FR-02-08
    InvestDialog     투자 금액 입력                                 FR-01-16
    ShopDialog       상점 (자금 부족 아이템 비활성화)
    ChoiceDialog     선택 이벤트 (선택지 중 하나)
  보여주는 창 (show_*) :
    EventDialog      행운·불행 이벤트 이름/설명/변화량               FR-02-06
    ResultDialog     최종 순위·점수·승자                            FR-02-09

모든 창은 모달(exec_)이라서, 창이 닫힐 때까지 다음 코드가 기다린다.
→ Controller에서 "값 = input.ask_job(...)" 처럼 한 줄로 쓸 수 있다.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (QDialog, QLabel, QPushButton, QLineEdit, QCheckBox, QRadioButton,
                             QButtonGroup, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
                             QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QWidget)

from common.adapter import (STAT_NAMES, read_character, read_job, read_item, read_event,
                            meets_requirements, pick, to_int)
from view import style

MAX_PLAYERS = 4
MIN_PLAYERS = 2
NAME_MAX_LEN = 10


def effect_lines(money: int = 0, happiness: int = 0, stats: dict = None) -> list:
    """변화량을 [(문구, 색), ...]로 만든다. 예) [("자금 +300,000원", 초록)]"""
    lines = []
    if money:
        lines.append((f"자금 {style.format_delta(money, '원')}", style.delta_color(money)))
    if happiness:
        lines.append((f"행복도 {style.format_delta(happiness)}", style.delta_color(happiness)))
    for name, v in (stats or {}).items():
        if v:
            lines.append((f"{name} {style.format_delta(v)}", style.delta_color(v)))
    return lines


def effect_html(money: int = 0, happiness: int = 0, stats: dict = None) -> str:
    parts = [f"<span style='color:{c}'>{t}</span>" for t, c in effect_lines(money, happiness, stats)]
    return " · ".join(parts) if parts else "변화 없음"


def stats_text(stats: dict) -> str:
    return " · ".join(f"{n} {stats.get(n, 0)}" for n in STAT_NAMES)


def _title(text: str, size: int = 16) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(f"font-size: {size}px; font-weight: bold;")
    return label


# ════════════════════════════════════════════════════════════════
# 묻는 창
# ════════════════════════════════════════════════════════════════
class SetupDialog(QDialog):
    """게임 설정: 인원(2~4, 라디오 버튼만 허용) + 이름 + NPC 지정"""

    def __init__(self, validator, parent=None):
        super().__init__(parent)
        self.setWindowTitle("게임 설정")
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
        self.rows = []
        for i in range(MAX_PLAYERS):
            label = QLabel(f"플레이어 {i + 1}")
            name = QLineEdit()
            name.setMaxLength(NAME_MAX_LEN)
            name.setPlaceholderText("이름 (1~10자)")
            npc = QCheckBox("NPC")
            npc.toggled.connect(lambda on, e=name: on and not e.text() and e.setText("NPC"))
            grid.addWidget(label, i, 0)
            grid.addWidget(name, i, 1)
            grid.addWidget(npc, i, 2)
            self.rows.append((label, name, npc))

        ok = QPushButton("다음: 캐릭터 선택")
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        cancel = QPushButton("취소")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)

        layout = QVBoxLayout(self)
        layout.addWidget(_title("인생마불 — 게임 설정"))
        layout.addLayout(count_row)
        layout.addLayout(grid)
        layout.addWidget(QLabel("NPC는 컴퓨터가 대신 플레이합니다."))
        layout.addLayout(buttons)
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


class CharacterDialog(QDialog):
    """캐릭터 선택: 능력치·고유 특성 표시, 이미 고른 캐릭터는 비활성화"""

    def __init__(self, player_name: str, characters, taken_ids, parent=None):
        super().__init__(parent)
        self.setWindowTitle("캐릭터 선택")
        self.selected_id = None

        grid = QGridLayout()
        for i, raw in enumerate(characters):
            c = read_character(raw)
            card = QFrame()
            card.setObjectName("charcard")
            card.setStyleSheet("QFrame#charcard { border: 1px solid #CCC; border-radius: 6px; }")
            name = _title(c.name, 15)
            stats = QLabel(f"{stats_text(c.stats)}  (합계 {sum(c.stats.values())})")
            trait = QLabel(f"특성: {c.trait}" if c.trait else "특성: 없음")
            trait.setWordWrap(True)
            button = QPushButton("선택")
            if c.id in taken_ids:   # 2.5 예외: 이미 선택된 캐릭터 → 버튼 비활성화
                button.setEnabled(False)
                button.setText("이미 선택된 캐릭터입니다.")
            button.clicked.connect(lambda _, cid=c.id: self._choose(cid))
            box = QVBoxLayout(card)
            box.addWidget(name)
            box.addWidget(stats)
            box.addWidget(trait)
            box.addWidget(button)
            grid.addWidget(card, i // 2, i % 2)

        layout = QVBoxLayout(self)
        layout.addWidget(_title(f"{player_name}님, 캐릭터를 고르세요"))
        layout.addLayout(grid)
        self.setMinimumWidth(520)

    def _choose(self, cid) -> None:
        self.selected_id = cid
        self.accept()


class JobDialog(QDialog):
    """직업 선택: 직업 목록·조건·월급 표시, 조건이 안 되는 직업은 비활성화"""

    def __init__(self, player_name: str, jobs, stats: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("직업 선택")
        self.selected_id = None

        grid = QGridLayout()
        for col, head in enumerate(["직업", "월급", "필요 능력치", ""]):
            grid.addWidget(QLabel(f"<b>{head}</b>"), 0, col)
        any_ok = False
        for row, raw in enumerate(jobs, start=1):
            job = read_job(raw)
            ok = meets_requirements(stats, job.requirements)
            any_ok = any_ok or ok
            need = ", ".join(f"{k} {v} 이상" for k, v in job.requirements.items()) or "조건 없음"
            labels = [QLabel(job.name), QLabel(style.format_money(job.salary)), QLabel(need)]
            for col, label in enumerate(labels):
                if not ok:
                    label.setStyleSheet(f"color: {style.TEXT_QUIET};")
                grid.addWidget(label, row, col)
            button = QPushButton("선택" if ok else "조건 부족")
            button.setEnabled(ok)
            button.clicked.connect(lambda _, jid=job.id: self._choose(jid))
            grid.addWidget(button, row, 3)

        layout = QVBoxLayout(self)
        layout.addWidget(_title(f"{player_name}님, 청년기 진입! 직업을 고르세요"))
        layout.addWidget(QLabel(f"내 능력치: {stats_text(stats)}"))
        layout.addLayout(grid)
        if not any_ok:
            layout.addWidget(QLabel("선택할 수 있는 직업이 없습니다."))
            close = QPushButton("확인")
            close.clicked.connect(self.reject)
            layout.addWidget(close)

    def _choose(self, jid) -> None:
        self.selected_id = jid
        self.accept()


class InvestDialog(QDialog):
    """투자 금액 입력. '투자'를 누르면 Input의 검사 함수로 확인하고, 통과해야 닫힌다."""

    def __init__(self, player_name: str, money: int, validator, parent=None):
        super().__init__(parent)
        self.setWindowTitle("투자")
        self.validator = validator     # text → 오류 메시지("" = 통과)
        self.skipped = False

        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("예) 500000")
        invest = QPushButton("투자")
        invest.setDefault(True)
        invest.clicked.connect(self.accept)
        skip = QPushButton("건너뛰기")
        skip.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(skip)
        buttons.addWidget(invest)

        layout = QVBoxLayout(self)
        layout.addWidget(_title(f"{player_name}님, 투자 기회입니다"))
        layout.addWidget(QLabel(f"보유 자금: {style.format_money(money)}"))
        layout.addWidget(QLabel("투자할 금액 (0 이상, 보유 자금 이하)"))
        layout.addWidget(self.amount_edit)
        layout.addLayout(buttons)

    def text(self) -> str:
        return self.amount_edit.text()

    def accept(self) -> None:
        message = self.validator(self.text()) if self.validator else ""
        if message:
            QMessageBox.warning(self, "입력 확인", message)
            self.amount_edit.selectAll()
            return
        super().accept()


class ShopDialog(QDialog):
    """상점: 아이템 목록, 자금이 모자라면 비활성화"""

    def __init__(self, player_name: str, money: int, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("상점")
        self.selected_index = None

        grid = QGridLayout()
        for col, head in enumerate(["아이템", "가격", "효과", ""]):
            grid.addWidget(QLabel(f"<b>{head}</b>"), 0, col)
        for row, raw in enumerate(items, start=1):
            item = read_item(raw)
            ok = item.price <= money
            grid.addWidget(QLabel(item.name), row, 0)
            grid.addWidget(QLabel(style.format_money(item.price)), row, 1)
            grid.addWidget(QLabel(effect_html(item.money, item.happiness, item.stats)), row, 2)
            button = QPushButton("구매" if ok else "자금 부족")
            button.setEnabled(ok)
            button.clicked.connect(lambda _, idx=row - 1: self._choose(idx))
            grid.addWidget(button, row, 3)

        leave = QPushButton("구매 안 함")
        leave.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(_title(f"{player_name}님, 상점에 도착했습니다"))
        layout.addWidget(QLabel(f"보유 자금: {style.format_money(money)}"))
        layout.addLayout(grid)
        layout.addWidget(leave, 0, Qt.AlignRight)

    def _choose(self, index: int) -> None:
        self.selected_index = index
        self.accept()


class ChoiceDialog(QDialog):
    """선택 이벤트: 선택지 버튼 중 하나를 고른다. options는 이벤트 모양(name, money, happiness…)"""

    def __init__(self, title: str, question: str, options, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.selected_index = None
        layout = QVBoxLayout(self)
        layout.addWidget(_title(question))
        for i, raw in enumerate(options):
            opt = read_event(raw)
            button = QPushButton(opt.name)
            button.clicked.connect(lambda _, idx=i: self._choose(idx))
            layout.addWidget(button)
            layout.addWidget(QLabel(effect_html(opt.money, opt.happiness, opt.stats)))

    def _choose(self, index: int) -> None:
        self.selected_index = index
        self.accept()


# ════════════════════════════════════════════════════════════════
# 보여주는 창
# ════════════════════════════════════════════════════════════════
class EventDialog(QDialog):
    """행운·불행 이벤트: 이름, 설명, 돈·행복도·능력치 변화량 (FR-02-06)"""
    HEADER = {"luck": ("행운!", "#F7DC6F"), "badluck": ("불행…", "#F1948A"),
              "item": ("아이템", "#D2B4DE"), "shop": ("상점", "#AED6F1")}

    def __init__(self, event, player_name: str = "", auto_close_ms: int = None, parent=None):
        super().__init__(parent)
        e = read_event(event)
        head_text, head_color = self.HEADER.get(e.kind, ("이벤트", "#D5D8DC"))
        self.setWindowTitle(head_text)

        header = QLabel(f"{player_name}  {head_text}" if player_name else head_text)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"background: {head_color}; font-size: 15px; font-weight: bold; padding: 8px;")
        name = _title(e.name, 18)
        name.setAlignment(Qt.AlignCenter)
        desc = QLabel(e.description)
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(name)
        layout.addWidget(desc)
        for text, color in effect_lines(e.money, e.happiness, e.stats):
            line = QLabel(text)
            line.setAlignment(Qt.AlignCenter)
            line.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
            layout.addWidget(line)
        ok = QPushButton("확인")
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        layout.addWidget(ok)
        self.setMinimumWidth(320)

        if auto_close_ms:   # NPC 차례일 때는 잠깐 보여 주고 자동으로 닫는다
            QTimer.singleShot(auto_close_ms, self.accept)


class ResultDialog(QDialog):
    """게임 종료: 점수 내림차순 순위 표 + 승자 (FR-02-09)"""

    def __init__(self, ranking, parent=None):
        super().__init__(parent)
        self.setWindowTitle("게임 결과")
        rows = []
        for r in ranking:
            rows.append({
                "name": str(pick(r, ("name", "player_name"), "?")),
                "money": to_int(pick(r, ("money", "player_money"), 0)),
                "happiness": to_int(pick(r, ("happiness", "player_happiness"), 0)),
                "score": to_int(pick(r, ("score",), 0)),
            })
        rows.sort(key=lambda x: x["score"], reverse=True)

        table = QTableWidget(len(rows), 5)
        table.setHorizontalHeaderLabels(["순위", "이름", "자금", "행복도", "점수"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i, r in enumerate(rows):
            cells = [f"{i + 1}위", r["name"], style.format_money(r["money"]),
                     str(r["happiness"]), f"{r['score']:,}"]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                if i == 0:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                table.setItem(i, col, item)

        winner = rows[0]["name"] if rows else "-"
        close = QPushButton("닫기")
        close.clicked.connect(self.accept)
        layout = QVBoxLayout(self)
        layout.addWidget(_title(f"우승: {winner}", 20))
        layout.addWidget(table)
        layout.addWidget(close, 0, Qt.AlignRight)
        self.setMinimumSize(520, 140 + 34 * max(1, len(rows)))


# ════════════════════════════════════════════════════════════════
# PopupView: 창을 띄우는 창구
# ════════════════════════════════════════════════════════════════
class PopupView:
    def __init__(self, parent: QWidget = None):
        self.parent = parent

    # ── 묻는 창: 값을 돌려준다 (취소하면 None) ──────────────
    def ask_setup(self, validator):
        dlg = SetupDialog(validator, self.parent)
        return dlg.values() if dlg.exec_() == QDialog.Accepted else None

    def ask_character(self, player_name, characters, taken_ids):
        dlg = CharacterDialog(player_name, characters, taken_ids, self.parent)
        dlg.exec_()
        return dlg.selected_id

    def ask_job(self, player_name, jobs, stats):
        dlg = JobDialog(player_name, jobs, stats, self.parent)
        dlg.exec_()
        return dlg.selected_id

    def ask_invest(self, player_name, money, validator):
        dlg = InvestDialog(player_name, money, validator, self.parent)
        return dlg.text() if dlg.exec_() == QDialog.Accepted else None

    def ask_shop(self, player_name, money, items):
        dlg = ShopDialog(player_name, money, items, self.parent)
        dlg.exec_()
        return dlg.selected_index

    def ask_choice(self, title, question, options):
        dlg = ChoiceDialog(title, question, options, self.parent)
        dlg.exec_()
        return dlg.selected_index

    # ── 보여주는 창 ─────────────────────────────────────────
    def show_event(self, event, player_name: str = "", auto_close_ms: int = None) -> None:
        EventDialog(event, player_name, auto_close_ms, self.parent).exec_()

    def show_result(self, ranking) -> None:
        ResultDialog(ranking, self.parent).exec_()

    def show_message(self, text: str, title: str = "알림") -> None:
        QMessageBox.information(self.parent, title, text)

    def show_warning(self, text: str, title: str = "입력 확인") -> None:
        QMessageBox.warning(self.parent, title, text)

    def show_error(self, text: str, title: str = "오류") -> None:
        QMessageBox.critical(self.parent, title, text)
