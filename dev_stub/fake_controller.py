"""
dev_stub/fake_controller.py  —  ⚠ 임시 코드 (팀원 Controller가 오기 전 테스트용)

목적 두 가지
  1) 내 View·Input·NPC를 실제 게임 흐름 순서대로 돌려 보기
  2) 팀원에게 "Controller에서 내 모듈을 이렇게 부르면 된다"는 사용 예시 보여 주기

흐름 (계획서 3.4 핵심 프로세스)
  begin_turn → (사람: 버튼 클릭 대기 / NPC: 잠깐 기다렸다 자동) → roll
  → show_dice → move_piece(애니메이션) → after_move(이동 반영·월급·단계 상승·칸 이벤트)
  → end_turn → 다음 플레이어 begin_turn … 모두 노년기를 마치면 결과 화면
"""
from __future__ import annotations

from PyQt5.QtCore import QObject, QTimer

from common.adapter import STAGES
from dev_stub.fake_model import CHARACTERS, JOBS, SHOP_ITEMS


class FakeController(QObject):
    def __init__(self, window, user_input, npc, model, parent=None):
        super().__init__(parent)
        self.window = window
        self.input = user_input
        self.npc = npc
        self.model = model
        self.turn = 0
        self.game_over = False

        # Input이 보내는 시그널 연결 (사용자가 먼저 행동하는 경우)
        self.input.roll_requested.connect(self.roll)
        self.input.invest_requested.connect(self.on_invest_clicked)

    # ── 준비 ─────────────────────────────────────────────
    def start(self) -> bool:
        configs = self.input.run_setup(CHARACTERS, npc_chooser=self.npc.choose_character)
        if configs is None:
            self.window.close()
            return False
        self.model.create_players(configs)
        self.window.set_board(self.model.board)
        self.window.set_players(self.model.players)
        self.window.add_log("게임 시작!")
        self.begin_turn()
        return True

    # ── 도우미 ───────────────────────────────────────────
    def current(self):
        return self.model.players[self.turn]

    def decider(self, p):
        """같은 질문에 사람은 Input이, 컴퓨터는 NPC가 대답한다"""
        return self.npc if p.is_npc else self.input

    def popup_wait(self, p):
        """NPC 차례 알림창은 자동으로 닫히게"""
        return self.npc.think_delay_ms * 2 if p.is_npc else None

    # ── 턴 진행 ──────────────────────────────────────────
    def begin_turn(self) -> None:
        p = self.current()
        if p.player_age >= 2:
            p.adult_turns += 1
        self.window.set_current_player(p)
        self.window.refresh(self.model.players)
        can_invest = self.model.can_invest(p)

        if p.is_npc:
            self.input.lock()                       # NPC 차례에는 사람 클릭 무시
            if can_invest:
                self.do_invest(p, self.npc.ask_invest(p, self.model.players))
            QTimer.singleShot(self.npc.think_delay_ms, self.roll)
        else:
            self.input.unlock(can_invest)
            if can_invest:
                self.window.add_log(f"{p.player_name}: 투자 기회! (투자하기 버튼)")

    def roll(self) -> None:
        if self.game_over:
            return
        p = self.current()
        d1, d2 = self.model.roll_dice()
        self.window.add_log(f"{p.player_name}: 주사위 {d1} + {d2} = {d1 + d2}")
        self.window.show_dice(d1, d2, on_done=lambda: self.move(p, d1 + d2))

    def move(self, p, steps: int) -> None:
        self.window.move_piece(p.player_id, p.player_position, steps,
                               on_done=lambda: self.after_move(p, steps))

    def after_move(self, p, steps: int) -> None:
        result = self.model.move(p, steps)
        self.window.refresh(self.model.players)

        if result["passed_start"]:
            self.window.add_log(f"{p.player_name}: 출발 칸 통과, 월급 {p.salary:,}원")
        if p.finished:
            self.window.add_log(f"{p.player_name}: 노년기를 마쳤습니다!")
        else:
            if result["stage_changed"]:
                self.window.add_log(f"{p.player_name}: {STAGES[p.player_age]} 진입")
                if STAGES[p.player_age] == "청년기" and not p.player_job:
                    self.choose_job(p)
            self.handle_tile(p)
        self.window.refresh(self.model.players)
        self.end_turn()

    def choose_job(self, p) -> None:
        job_id = self.decider(p).ask_job(p, JOBS)
        self.model.set_job(p, job_id)
        self.window.add_log(f"{p.player_name}: 직업 → {p.player_job}")

    def handle_tile(self, p) -> None:
        kind = self.model.tile_kind(p)
        if kind in ("luck", "badluck"):
            event = self.model.draw_event(p, kind)
        elif kind == "item":
            event = self.model.draw_item()
        elif kind == "shop":
            index = self.decider(p).ask_shop(p, SHOP_ITEMS)
            if index is None:
                self.window.add_log(f"{p.player_name}: 상점에서 아무것도 사지 않음")
                return
            item = SHOP_ITEMS[index]
            self.model.apply(p, {**item, "money": -item["price"]})
            self.window.add_log(f"{p.player_name}: {item['name']} 구매")
            return
        else:
            return
        self.model.apply(p, event)
        self.window.refresh(self.model.players)
        self.window.add_log(f"{p.player_name}: {event['name']}")
        self.window.show_event(event, p.player_name, self.popup_wait(p))

    def on_invest_clicked(self) -> None:
        p = self.current()
        self.do_invest(p, self.input.ask_invest(p))

    def do_invest(self, p, amount: int) -> None:
        if amount <= 0:
            self.window.add_log(f"{p.player_name}: 투자 건너뜀")
            return
        result = self.model.invest(p, amount)
        self.window.refresh(self.model.players)
        self.window.add_log(f"{p.player_name}: {result['description']}")
        self.window.show_event(result, p.player_name, self.popup_wait(p))

    def end_turn(self) -> None:
        if self.model.all_finished():
            self.game_over = True
            self.input.lock()
            self.window.add_log("게임 종료!")
            self.window.show_result(self.model.ranking())
            return
        n = len(self.model.players)
        for _ in range(n):                     # 노년기를 마친 플레이어는 건너뛴다
            self.turn = (self.turn + 1) % n
            if not self.current().finished:
                break
        self.begin_turn()
