"""
dev_stub/fake_controller.py  —  가짜 Controller (팀장 데모·테스트용)

규칙 문서 '한 턴의 순서' 8단계를 그대로 따라 View·Input·NPC를 부른다.
팀원이 controller/game_controller.py를 만들 때 "내 모듈을 어떻게 부르는지" 보는 예시이기도 하다.

  1 휴식 확인 → 2 주사위 → 3 국가고시(의대생) → 4 이동(출발 칸: 단계·직업·고유 장치)
  → 5 칸 효과 → 6 매 턴 수입 → 7 투자 → 8 다음 사람

지키는 약속
  - 사람/NPC 구분은 decider() 한 곳에서만 한다. (Input과 NPC는 ask_* 함수 모양이 같다)
  - 기다림은 QTimer로만 한다 (time.sleep 금지). 창(ask_*, show_*)은 모달이라 닫힐 때까지 기다린다.
  - fast=True면 애니메이션·기다림을 건너뛴다 (자동 테스트용).
"""
from __future__ import annotations

import random

from PyQt5.QtCore import QObject, QTimer

from common.constants import STAGES, EXAM_LEVEL_NAMES
from user_input import Input
from npc import NPC
from dev_stub import fake_data as D
from dev_stub.fake_model import FakeGame, ADULT, MIDDLE, OLD

NPC_EVENT_MS = 1600          # NPC 차례 이벤트 카드는 저절로 닫힌다


class FakeController(QObject):
    def __init__(self, window, quick: bool = True, seed: int = None, fast: bool = False):
        super().__init__(window)
        self.window = window
        self.quick, self.fast = quick, fast
        self.rng = random.Random(seed)
        self.input = Input(window)
        self.npc = NPC(random.Random(seed))
        self.game = None
        self.finished_callback = None            # 테스트용: 게임이 끝나면 부른다
        self.input.roll_requested.connect(self.roll)
        self.input.invest_requested.connect(self.human_invest)
        self.input.end_turn_requested.connect(self.next_player)

    # ── 도우미 ──────────────────────────────────────────────────
    def decider(self, p):
        """사람이면 Input, NPC면 NPC. 함수 이름과 반환값이 같아서 그대로 바꿔 끼운다."""
        return self.npc if p.is_npc else self.input

    def later(self, ms: int, fn) -> None:
        QTimer.singleShot(0 if self.fast else ms, fn)

    def show(self, p, event) -> None:
        """이벤트 카드 + 기록. NPC 차례 카드는 저절로 닫힌다."""
        if not event:
            return
        self.window.show_event(event, p.player_name, NPC_EVENT_MS if p.is_npc else None)
        self.window.add_log(f"{p.player_name}: {event['name']}")
        self.window.refresh(self.game.players)

    # ── 게임 시작 ───────────────────────────────────────────────
    def start(self, rows=None) -> None:
        rows = rows or self.input.run_setup(D.CHARACTERS, self.npc.choose_character)
        if rows is None:                       # 설정 창을 닫으면 끝낸다
            self.window.close()
            return
        self.game = FakeGame(rows, random.Random(self.rng.random()), self.quick)
        self.window.set_board(self.game.board)
        self.window.set_players(self.game.players)
        self.window.set_round(1)
        self.window.show_news(self.game.opening_news)
        self.window.set_trend(self.game.trend_label())
        self.later(300, self.start_turn)

    # ── 1 휴식 확인 ─────────────────────────────────────────────
    def start_turn(self) -> None:
        p = self.game.current_player()
        self.window.set_current_player(p)
        self.window.refresh(self.game.players)
        if p.skip_turns > 0:
            p.skip_turns -= 1
            self.window.add_log(f"{p.player_name}: 쉬는 턴 (수입 없음)")
            self.later(700, self.next_player)
            return
        self.game.start_turn(p)
        if p.is_npc:
            self.input.lock()                  # NPC 차례에는 클릭 무시
            self.later(self.npc.think_delay_ms(), self.roll)
        else:
            self.input.unlock()

    # ── 2 주사위 ────────────────────────────────────────────────
    def roll(self) -> None:
        d1, d2 = self.game.roll_dice()
        self.window.add_log(f"{self.game.current_player().player_name}: 주사위 {d1} + {d2}")
        if self.fast:
            self.after_dice(d1, d2)
        else:
            self.window.show_dice(d1, d2, on_done=lambda: self.after_dice(d1, d2))

    def after_dice(self, d1: int, d2: int) -> None:
        p = self.game.current_player()
        if p.job_state == "student":           # 3 국가고시
            self.exam(p)
        result = self.game.move(p, d1 + d2)    # 4 이동 (Model 먼저 바꾸고, 화면은 애니메이션)
        done = lambda: self.after_move(p, result, d1 + d2)     # noqa: E731
        if self.fast:
            done()
        else:
            self.window.move_piece(p.player_id, result["from"], d1 + d2, on_done=done)

    # ── 3 국가고시 ──────────────────────────────────────────────
    def exam(self, p) -> None:
        q = self.game.exam_question(p)
        level, limit = p.exam_level, self.game.exam_time_limit(p)
        level_name = EXAM_LEVEL_NAMES[level]
        answer = self.decider(p).ask_exam_answer(p, q, limit, level_name)
        if p.is_npc:                           # NPC는 '고민 중...' 뒤 고른 답을 보여 준다
            self.window.show_exam_npc(p.player_name, q, level, level_name, limit, answer, self.npc.think_delay_ms())
        result = self.game.grade_exam(p, q, answer)
        self.show(p, result)
        if result["passed"]:
            return
        if level < 5 and self.decider(p).ask_retry_exam(p, level):
            self.game.retry_exam(p)
            return
        self.game.give_up_exam(p)
        self.choose_job(p, exclude=("doctor",), heading=f"{p.player_name}님, 의사 대신 다른 직업을 고르세요")

    # ── 4 이동 뒤: 출발 칸 ──────────────────────────────────────
    def after_move(self, p, result: dict, dice_sum: int) -> None:
        self.window.refresh(self.game.players)
        if result["passed_start"]:
            self.passed_start(p, result)
        if p.finished:
            self.window.add_log(f"{p.player_name}: 인생 완주! 차례에서 빠진다")
            self.later(500, self.next_player)
            return
        self.tile_effect(p)                                   # 5
        self.income(p, result["steps"], dice_sum)             # 6
        self.invest_step(p)                                   # 7

    def passed_start(self, p, result: dict) -> None:
        old, new = result["old_stage"], result["new_stage"]
        if p.finished:
            if p.job_id == "freelancer" and p.gig is not None:
                self.show(p, self.game.settle_gig(p))
            return
        if new != old:
            self.show(p, {"kind": "info", "name": f"{STAGES[new]} 진입!", "description": f"{p.player_lap}바퀴째를 마쳤다."})
        if new == ADULT and old != ADULT:
            self.choose_job(p)
            return
        if new == MIDDLE and old != MIDDLE and p.job_state == "student":
            self.show(p, dict(self.game.set_job(p, "freelancer"), name="국가고시 시간 초과... 프리랜서가 됐다"))
            self.choose_gig(p)
            return
        if new == OLD and old != OLD:
            if p.job_id == "freelancer":
                self.show(p, self.game.settle_gig(p))         # 마지막 의뢰 정산, 새 의뢰 없음
            if p.job_id == "artist":
                art = self.game.make_artwork(p)
                p.artworks.append(art)
                self.show(p, self.game.retrospective(p))
            return
        if p.job_state != "employed":
            return
        card = self.game.card(p, "job_change")                # 직업 변경권
        if card:
            job_id = self.decider(p).ask_job(p, self.game.jobs_for(p), exclude=("doctor", p.job_id),
                                             allow_keep=True, heading="직업 변경권: 다른 직업으로 바꿀까요?")
            if job_id:
                self.game.take_card(p, "job_change")
                self.show(p, self.game.set_job(p, job_id))
                self.after_job(p)
                return
        if p.job_id == "business":
            self.switch_business(p)
        elif p.job_id == "freelancer":
            self.show(p, self.game.settle_gig(p))
            self.choose_gig(p)
        elif p.job_id == "artist":
            self.artwork(p)

    def choose_job(self, p, exclude=(), heading: str = "") -> None:
        job_id = self.decider(p).ask_job(p, self.game.jobs_for(p), exclude=exclude, heading=heading)
        self.show(p, self.game.set_job(p, job_id))
        self.after_job(p)

    def after_job(self, p) -> None:
        """직업을 고른 순간: 사업가는 업종, 프리랜서는 첫 의뢰"""
        if p.job_id == "business":
            bid = self.decider(p).ask_business(p, D.BUSINESSES, self.game.trend, self.game.trend_rounds_left)
            self.game.set_business(p, bid)
            self.window.add_log(f"{p.player_name}: 업종 {p.shop_type['name']}")
        elif p.job_id == "freelancer":
            self.choose_gig(p)

    def switch_business(self, p) -> None:
        cost = D.SETTINGS["switch_cost"]
        bid = self.decider(p).ask_switch_business(p, D.BUSINESSES, self.game.business_id(p), self.game.trend,
                                                  self.game.trend_rounds_left, cost)
        if bid:
            self.game.set_business(p, bid, cost)
            self.show(p, {"kind": "business", "name": f"업종 변경: {p.shop_type['name']}", "money": -cost})

    def choose_gig(self, p) -> None:
        gig_id = self.decider(p).ask_gig(p, self.game.gig_cards(), D.SETTINGS["rest_happiness"])
        self.game.take_gig(p, gig_id)
        self.window.add_log(f"{p.player_name}: 의뢰 {p.gig['name'] if isinstance(p.gig, dict) else '이번 바퀴는 쉰다'}")

    def artwork(self, p) -> None:
        art = self.game.make_artwork(p)
        sell_id = self.decider(p).ask_artwork(p, art, list(p.artworks))
        self.show(p, self.game.place_artwork(p, art, sell_id))

    # ── 5 칸 효과 ───────────────────────────────────────────────
    def tile_effect(self, p) -> None:
        kind = self.game.board[p.player_position]
        if kind == "luck":
            double = self.game.take_card(p, "double_luck")
            self.show(p, self.game.apply_event(p, self.game.draw_event(p, "luck"), 2 if double else 1))
        elif kind == "badluck":
            template = self.game.draw_event(p, "badluck")
            card = self.game.card(p, "bad_to_good")
            if card and self.decider(p).ask_use_card(p, card, self.game.preview(p, template)):
                self.game.take_card(p, "bad_to_good")
                template = self.game.draw_event(p, "luck")
            self.show(p, self.game.apply_event(p, template))
        elif kind == "golden_key":
            self.show(p, self.game.draw_golden_key(p))
        elif kind == "shop":
            items = self.game.shop_items(p)
            index = self.decider(p).ask_shop(p, items, self.game.jobs_for(p))
            if index is not None:
                self.show(p, self.game.buy(p, items[index]))
        elif kind == "rest":
            p.skip_turns = 1
            self.show(p, {"kind": "info", "name": "휴식", "description": "다음 턴은 쉰다. 그 턴 수입은 없다."})

    # ── 6 매 턴 수입 ────────────────────────────────────────────
    def income(self, p, steps: int, dice_sum: int) -> None:
        result = self.game.apply_income(p, steps, dice_sum)
        if result["event"]:
            self.show(p, result["event"])
        if result["money"] or result["happiness"]:
            self.window.show_income(p.player_id, result["money"], result["happiness"])
        self.window.refresh(self.game.players)

    # ── 7 투자 ──────────────────────────────────────────────────
    def invest_step(self, p) -> None:
        for event in self.game.settle_investments(p):
            self.show(p, event)
        can_invest = self.game.invest_ready(p)
        if p.is_npc:
            if can_invest:
                choice = self.npc.ask_invest(p, self.game.companies, self.game.players)
                if choice:
                    self.show(p, self.game.invest(p, choice["company_id"], choice["amount"]))
            self.later(400, self.next_player)
        elif can_invest:
            self.input.unlock_actions(can_invest)       # '턴 마치기'를 누를 때까지 기다린다
        else:
            self.later(300, self.next_player)

    def human_invest(self) -> None:
        p = self.game.current_player()
        choice = self.input.ask_invest(p, self.game.companies, self.game.players)
        if choice:
            self.show(p, self.game.invest(p, choice["company_id"], choice["amount"]))
        self.input.unlock_actions(False)

    # ── 8 다음 사람 ─────────────────────────────────────────────
    def next_player(self) -> None:
        self.input.lock()
        for headline in self.game.next_turn():
            self.window.show_news(headline)
            self.window.set_trend(self.game.trend_label())
        self.window.set_round(self.game.round)
        if self.game.is_over():
            self.game_over()
            return
        self.later(250, self.start_turn)

    def game_over(self) -> None:
        self.game.finish()
        self.window.refresh(self.game.players)
        again = self.window.show_result(self.game.ranking())
        if self.finished_callback:
            self.finished_callback(self.game)
            return
        if again:
            self.start()
        else:
            self.window.close()
