"""
user_input/input_handler.py  —  Input: 사용자 입력 감지 및 변환 (FR-03-01 ~ FR-03-03)

역할 나누기
  View   : 버튼·입력칸을 "보여 주기만" 한다.
  Input  : 그 버튼이 눌렸는지 "감지"하고, 입력값을 "검사·변환"해서 Controller에 넘긴다.
  Controller : Input이 넘겨준 깨끗한 값(정수, id 등)만 보고 게임을 진행한다.

Input이 Controller에 값을 넘기는 두 가지 방법
  ① 시그널 (사용자가 먼저 행동하는 경우)
       roll_requested    : 주사위 버튼 클릭
       invest_requested  : 투자 버튼 클릭
  ② 반환값 (Controller가 먼저 물어보는 경우, 창이 닫힐 때까지 기다림)
       run_setup()   → 플레이어 설정 목록
       ask_job()     → 직업 id
       ask_invest()  → 투자 금액(int, 0 = 건너뛰기)
       ask_shop()    → 아이템 번호 / None
       ask_choice()  → 선택지 번호
  ※ NPC 차례에는 같은 질문을 NPC 객체에 물어보면 된다. (npc.ask_job … 함수 이름·반환값이 같음)

폴더 이름을 'input'으로 하지 않은 이유: 파이썬 내장 함수 input()과 이름이 겹쳐 헷갈리기 때문.
"""
from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal

from common.adapter import read_player

NAME_MIN_LEN, NAME_MAX_LEN = 1, 10
MAX_NPC = 1     # 계획서: "플레이어 중 한 명을 NPC로 대체"

# 2.5 예외 처리 표의 출력 메시지
MSG_NAME_EMPTY = "이름을 입력하세요."
MSG_NAME_DUP = "이미 사용 중인 이름입니다."
MSG_NAME_LONG = f"이름은 {NAME_MAX_LEN}자 이하로 입력하세요."
MSG_NPC_LIMIT = f"NPC는 최대 {MAX_NPC}명까지 정할 수 있습니다."
MSG_NOT_NUMBER = "숫자를 입력하세요."
MSG_NEGATIVE = "0 이상의 금액을 입력하세요."
MSG_OVER_MONEY = "보유 금액을 초과할 수 없습니다."


# ════════════════════════════════════════════════════════════════
# 검사·변환 함수 (Qt와 무관한 순수 함수 → 단위 테스트하기 쉽다)
#   반환값: 오류 메시지 문자열, 문제가 없으면 "" (빈 문자열)
# ════════════════════════════════════════════════════════════════
def validate_name(name: str, used_names) -> str:
    name = (name or "").strip()
    if len(name) < NAME_MIN_LEN:
        return MSG_NAME_EMPTY
    if len(name) > NAME_MAX_LEN:
        return MSG_NAME_LONG
    if name in used_names:
        return MSG_NAME_DUP
    return ""


def validate_setup(rows, max_npc: int = MAX_NPC) -> str:
    """rows: [{"name": "철수", "is_npc": False}, ...]"""
    used = []
    for i, row in enumerate(rows, start=1):
        message = validate_name(row.get("name", ""), used)
        if message:
            return f"플레이어 {i}: {message}"
        used.append(row["name"].strip())
    if sum(1 for r in rows if r.get("is_npc")) > max_npc:
        return MSG_NPC_LIMIT
    return ""


def parse_amount(text: str):
    """'1,000,000원' 같은 입력도 받아 준다. 숫자가 아니면 None."""
    cleaned = (text or "").strip().replace(",", "").replace("원", "").replace(" ", "")
    if cleaned.startswith("-") and cleaned[1:].isdigit():
        return -int(cleaned[1:])
    return int(cleaned) if cleaned.isdigit() else None


def validate_invest_text(text: str, money: int) -> str:
    amount = parse_amount(text)
    if amount is None:
        return MSG_NOT_NUMBER
    if amount < 0:
        return MSG_NEGATIVE
    if amount > max(0, money):
        return MSG_OVER_MONEY
    return ""


# ════════════════════════════════════════════════════════════════
# Input 클래스
# ════════════════════════════════════════════════════════════════
class Input(QObject):
    roll_requested = pyqtSignal()      # 주사위 굴리기 클릭 (FR-03-02)
    invest_requested = pyqtSignal()    # 투자하기 클릭

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.popup = window.popup_view
        self._locked = True            # 게임 시작 전에는 잠겨 있다

        # View의 버튼 클릭을 감지한다
        window.dice_view.roll_button.clicked.connect(self._on_roll_clicked)
        window.dice_view.invest_button.clicked.connect(self._on_invest_clicked)
        self.lock()

    # ── 잠금: NPC 차례·말 이동 중에는 클릭을 막는다 ──────────────
    def lock(self) -> None:
        """2.5 예외: NPC 턴 클릭 무시, 이동 중 주사위 클릭 차단"""
        self._locked = True
        self.window.set_roll_enabled(False)
        self.window.set_invest_enabled(False)

    def unlock(self, can_invest: bool = False) -> None:
        """사람 플레이어 차례가 시작될 때 Controller가 부른다."""
        self._locked = False
        self.window.set_roll_enabled(True)
        self.window.set_invest_enabled(can_invest)   # 투자 가능한 턴이 아니면 비활성화

    def is_locked(self) -> bool:
        return self._locked

    # ── 버튼 클릭 감지 → 시그널로 변환 ──────────────────────────
    def _on_roll_clicked(self) -> None:
        if self._locked:          # 버튼이 꺼져 있어도 한 번 더 막는다 (이중 방어)
            return
        self.lock()               # 한 번 누르면 다음 턴까지 잠금 (2.4: 버튼 비활성화)
        self.roll_requested.emit()

    def _on_invest_clicked(self) -> None:
        if self._locked:
            return
        self.window.set_invest_enabled(False)   # 한 턴에 한 번만
        self.invest_requested.emit()

    # ── Controller가 물어보는 함수들 (창을 띄우고 결과를 돌려줌) ──
    def run_setup(self, characters, npc_chooser=None):
        """게임 설정 → 캐릭터 선택까지 받아서 돌려준다. 취소하면 None.

        반환 예) [{"name": "철수", "is_npc": False, "character_id": "student"}, ...]
        npc_chooser: NPC 캐릭터를 대신 골라 줄 함수 (보통 npc.choose_character)
        """
        rows = self.popup.ask_setup(validate_setup)
        if rows is None:
            return None
        taken = []
        for row in rows:
            row["name"] = row["name"].strip()
            if row["is_npc"] and npc_chooser is not None:
                cid = npc_chooser(characters, taken)
            else:
                cid = self.popup.ask_character(row["name"], characters, taken)
            if cid is None:          # 캐릭터 선택 창을 닫으면 설정 취소
                return None
            taken.append(cid)
            row["character_id"] = cid
        return rows

    def ask_job(self, player, jobs):
        """청년기 진입 시 직업 선택. 직업 id를 돌려준다. (선택 가능한 직업이 없으면 None)"""
        info = read_player(player)
        return self.popup.ask_job(info.name, jobs, info.stats)

    def ask_invest(self, player, others=(), expected_return_percent: int = 10) -> int:
        """투자 금액을 정수로 돌려준다. 건너뛰면 0.
        (others, expected_return_percent는 NPC.ask_invest와 모양을 맞추려고 있는 인자. 사람은 안 씀)"""
        info = read_player(player)
        text = self.popup.ask_invest(info.name, info.money,
                                     lambda t: validate_invest_text(t, info.money))
        if text is None:
            return 0
        return parse_amount(text) or 0

    def ask_shop(self, player, items):
        info = read_player(player)
        return self.popup.ask_shop(info.name, info.money, items)

    def ask_choice(self, player, title: str, question: str, options):
        index = self.popup.ask_choice(title, question, options)
        return 0 if index is None else index
