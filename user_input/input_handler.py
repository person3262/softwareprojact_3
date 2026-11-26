"""
user_input/input_handler.py  —  Input: 사용자 입력 감지 및 변환 (FR-03-01 ~ FR-03-03)

역할 나누기
  View   : 버튼·입력칸을 "보여 주기만" 한다.
  Input  : 그 버튼이 눌렸는지 "감지"하고, 입력값을 "검사·변환"해서 Controller에 넘긴다.
  Controller : Input이 넘겨준 깨끗한 값(정수, id 등)만 보고 게임을 진행한다.

Input이 Controller에 값을 넘기는 두 가지 방법
  ① 시그널 (사용자가 먼저 행동하는 경우)
       roll_requested     : 주사위 버튼 클릭
       invest_requested   : 투자 버튼 클릭
       end_turn_requested : '턴 마치기' 클릭 (투자 단계 끝)
     버튼 켜기·끄기: lock() / unlock() / unlock_actions(can_invest)
  ② 반환값 (Controller가 먼저 물어보는 경우, 창이 닫힐 때까지 기다림)
       run_setup()            → [{"name", "is_npc", "character_id"}] / None
       ask_job()              → 직업 id / None(지금 직업 유지)
       ask_exam_answer()      → 1~4 / None(시간 초과)
       ask_retry_exam()       → True(재수) / False(포기)
       ask_business()         → 업종 id
       ask_switch_business()  → 바꿀 업종 id / None(그대로)
       ask_gig()              → 의뢰 카드 id / None(쉬기)
       ask_artwork()          → 팔 작품 id / None(모두 보관)
       ask_shop()             → 상품 번호 / None
       ask_invest()           → {"company_id", "amount"} / None(건너뛰기)
       ask_choice()           → 선택지 번호
       ask_use_card()         → True / False
  ※ NPC 차례에는 같은 질문을 NPC 객체에 물어보면 된다. (npc.ask_job … 함수 이름·인자·반환값이 같음)

폴더 이름을 'input'으로 하지 않은 이유: 파이썬 내장 함수 input()과 이름이 겹쳐 헷갈리기 때문.
"""
from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal

from common.constants import STUDIO_SIZE
from common.adapter import (read_player, read_question, read_event, read_card, read_company, read_business,
                            read_job, meets_requirements, pick)
from user_input.validators import (validate_setup, validate_invest, validate_switch, validate_exam_answer,
                                   parse_amount)

# 예전 import 경로 호환: from user_input.input_handler import validate_setup ...
from user_input.validators import *   # noqa: F401,F403


class Input(QObject):
    roll_requested = pyqtSignal()      # 주사위 굴리기 클릭 (FR-03-02)
    invest_requested = pyqtSignal()    # 투자하기 클릭 (FR-01-16)
    end_turn_requested = pyqtSignal()  # '턴 마치기' 클릭 (한 턴의 순서 7번이 끝남)

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.popup = window.popup_view
        self._locked = True            # 게임 시작 전에는 잠겨 있다
        self._end_mode = False         # True면 큰 버튼이 '턴 마치기'

        # View의 버튼 클릭을 감지한다
        dice = window.dice_view
        dice.roll_button.clicked.connect(self._on_roll_clicked)
        dice.invest_button.clicked.connect(self._on_invest_clicked)
        self.lock()

    # ── 잠금: NPC 차례·말 이동 중에는 클릭을 막는다 ──────────────
    def lock(self) -> None:
        """예외 처리: NPC 차례의 클릭 무시, 말이 움직이는 동안 주사위 클릭 차단"""
        self._locked = True
        self._set_end_mode(False)
        self.window.set_roll_enabled(False)
        self.window.set_invest_enabled(False)

    def unlock(self) -> None:
        """사람 플레이어 차례가 시작될 때 Controller가 부른다. '주사위 굴리기'만 켠다."""
        self._locked = False
        self._set_end_mode(False)
        self.window.set_roll_enabled(True)

    def unlock_actions(self, can_invest: bool = False) -> None:
        """한 턴의 순서 7번(투자): '턴 마치기'와 투자 버튼을 켠다.
        사용자가 투자를 마치고(또는 건너뛰고) '턴 마치기'를 누르면 end_turn_requested가 나간다."""
        self._locked = False
        self._set_end_mode(True)
        self.window.set_roll_enabled(True)
        self.window.set_invest_enabled(can_invest)              # 투자 기회 턴이 아니면 꺼짐

    def _set_end_mode(self, on: bool) -> None:
        self._end_mode = on
        self.window.set_end_mode(on)

    def is_locked(self) -> bool:
        return self._locked

    # ── 버튼 클릭 감지 → 시그널로 변환 ──────────────────────────
    def _on_roll_clicked(self) -> None:
        if self._locked:          # 버튼이 꺼져 있어도 한 번 더 막는다 (이중 방어)
            return
        ending = self._end_mode
        self.lock()               # 한 번 누르면 잠금: 두 번 굴리기·이동 중 클릭 방지
        (self.end_turn_requested if ending else self.roll_requested).emit()

    def _on_invest_clicked(self) -> None:
        if self._locked:
            return
        self.window.set_invest_enabled(False)   # 한 턴에 한 번만
        self.invest_requested.emit()

    # ── 게임 준비 ───────────────────────────────────────────────
    def run_setup(self, characters, npc_chooser=None):
        """게임 설정 → 캐릭터 선택까지 받아서 돌려준다. 취소하면 None.

        반환 예) [{"name": "정민", "is_npc": False, "character_id": "scholar"}, ...]
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

    # ── 직업 ────────────────────────────────────────────────────
    def ask_job(self, player, jobs, exclude=(), allow_keep: bool = False, heading: str = ""):
        """직업 선택. 직업 id를 돌려준다.
        exclude   : 고를 수 없는 직업 id (예: 국가고시를 포기했으면 ("doctor",))
        allow_keep: 직업 변경권처럼 '지금 직업 유지'가 가능하면 True → 유지하면 None
        jobs의 requirements는 Model이 캐릭터 특성(평범이 -10)을 반영해서 넘겨준다."""
        info = read_player(player)
        chosen = self.popup.ask_job(info.name, jobs, info.stats, tuple(exclude), allow_keep, heading)
        if chosen is None and not allow_keep:
            # (이중 방어) 창이 값 없이 닫히면 고를 수 있는 첫 직업. 프리랜서는 조건이 없어서 항상 있다.
            able = [read_job(j).id for j in jobs
                    if read_job(j).id not in exclude and meets_requirements(info.stats, read_job(j).requirements)]
            chosen = able[0] if able else None
        return chosen

    def ask_exam_answer(self, player, question, time_limit: int, level_name: str = ""):
        """의사 국가고시 한 문제. 1~4, 시간 초과면 None (12.2: 첫 입력만 인정)"""
        info = read_player(player)
        q = read_question(question)
        answer = self.popup.ask_exam(info.name, question, q.level, level_name, time_limit)
        return validate_exam_answer(answer)

    def ask_retry_exam(self, player, level: int) -> bool:
        """국가고시에 떨어졌을 때: True = 재수한다, False = 포기한다"""
        return bool(self.popup.ask_confirm(
            "국가고시", f"{level}단계에서 떨어졌어요. 재수할까요?",
            "재수하면 다음 턴에 한 단계 쉬운 문제가 나와요. 포기하면 의사를 뺀 다른 직업을 골라요.",
            "재수한다", "포기한다"))

    # ── 사업가 업종 (규칙 문서: 직업별 고유 장치) ─────────────────
    def ask_business(self, player, businesses, trend=None, rounds_left: int = 0):
        """사업가가 된 순간 업종을 고른다. 업종 id를 돌려준다. 창을 닫으면 첫 번째 업종."""
        info = read_player(player)
        ids = [read_business(b).id for b in businesses]
        chosen = self.popup.ask_business(info.name, businesses, trend, rounds_left)
        return chosen if chosen in ids else (ids[0] if ids else None)

    def ask_switch_business(self, player, businesses, current=None, trend=None, rounds_left: int = 0,
                            cost: int = 1000):
        """출발 칸을 지날 때 업종을 바꿀지 묻는다. 바꿀 업종 id, 그대로 하면 None.
        비용 부족·같은 업종은 validate_switch가 막는다 (12.2 예외 처리)."""
        info = read_player(player)
        ids = [read_business(b).id for b in businesses]
        check = lambda new_id: validate_switch(info.money, current, new_id, cost, ids)   # noqa: E731
        chosen = self.popup.ask_switch_business(info.name, businesses, current, trend, rounds_left,
                                                info.money, cost, check)
        if chosen is None or check(chosen):
            return None                     # 그대로 하기, 또는 (이중 방어) 검사 실패
        return chosen

    # ── 프리랜서 · 예술가 ─────────────────────────────────────────
    def ask_gig(self, player, cards, rest_happiness: int = 50):
        """의뢰 카드 3장 중 하나: 카드 id, '이번 바퀴는 쉰다'면 None"""
        info = read_player(player)
        ids = [str(pick(c, ("id",), "")) for c in cards]
        chosen = self.popup.ask_gig(info.name, cards, info.stats, rest_happiness)
        return chosen if chosen in ids else None

    def ask_artwork(self, player, artwork, studio, studio_size: int = STUDIO_SIZE):
        """작품 완성: 팔 작품 id, 모두 보관하면 None.
        작업실이 꽉 차 있으면 창이 팔 작품을 고를 때까지 닫히지 않는다 (12.2)."""
        info = read_player(player)
        ids = [str(pick(a, ("id",), "")) for a in list(studio or []) + [artwork]]
        chosen = self.popup.ask_artwork(info.name, artwork, studio, studio_size)
        if chosen is None and len(studio or []) >= studio_size:
            chosen = ids[-1]               # (이중 방어) 꽉 찼는데 값이 없으면 새 작품을 판다
        return chosen if chosen in ids else None

    # ── 돈 쓰기 ─────────────────────────────────────────────────
    def ask_shop(self, player, items, jobs=()):
        """상점: 상품 번호 / 안 사면 None. (jobs는 NPC.ask_shop과 모양을 맞추려는 인자, 사람은 안 씀)"""
        info = read_player(player)
        index = self.popup.ask_shop(info.name, info.money, items)
        return index if isinstance(index, int) and 0 <= index < len(items) else None

    def ask_invest(self, player, companies, others=()):
        """투자: {"company_id": id, "amount": 만원} / 건너뛰면 None. 금액 0도 건너뛰기로 본다.
        (others는 NPC.ask_invest와 모양을 맞추려고 있는 인자. 사람은 안 씀)"""
        info = read_player(player)
        ids = [read_company(c).id for c in companies]
        result = self.popup.ask_invest(info.name, info.money, companies,
                                       lambda cid, amount: validate_invest(cid, amount, info.money, ids))
        if not result:
            return None
        company_id, amount = result
        amount = parse_amount(amount) or 0
        if amount <= 0 or validate_invest(company_id, amount, info.money, ids):
            return None
        return {"company_id": company_id, "amount": amount}

    # ── 이벤트 ──────────────────────────────────────────────────
    def ask_choice(self, player, title: str, question: str, options):
        index = self.popup.ask_choice(title, question, options)
        return 0 if index is None else index

    def ask_use_card(self, player, card, event=None) -> bool:
        """보관 중인 황금열쇠를 지금 쓸지. 예) 불행 칸에서 '불운→행운 변경권을 쓸까요?'"""
        c = read_card(card)
        detail = ""
        if event is not None:
            e = read_event(event)
            detail = f"이번 이벤트: {e.name}"
        return bool(self.popup.ask_confirm("황금열쇠", f"{c.name}을(를) 쓸까요?", detail, "쓸래요", "아껴 둘래요"))
