"""
npc/npc.py  —  NPC: 플레이어 한 자리를 대신하는 컴퓨터 (FR-04-01, 3.4 NPC 행동 결정 알고리즘)

핵심 아이디어: "같은 질문에 사람은 Input이, 컴퓨터는 NPC가 대답한다"
  Input.ask_job(player, jobs)   ↔  NPC.ask_job(player, jobs)
  Input.ask_invest(player, …)   ↔  NPC.ask_invest(player, …)
  Input.ask_shop(player, items) ↔  NPC.ask_shop(player, items)
  Input.ask_choice(player, …)   ↔  NPC.ask_choice(player, …)
  → Controller는  answer = (npc if 플레이어가 NPC else input).ask_job(...)  한 줄로 처리할 수 있다.

판단 기준: 최종 점수(돈과 행복도의 가중합)를 가장 많이 올리는 쪽을 고른다.
  점수 = 자금 // money_unit + 행복도 × happiness_weight
  (기본값: 1만원 = 1점, 행복도 1 = 10점 → Model의 최종 점수 공식과 반드시 맞출 것)

NPC는 Qt를 쓰지 않는 순수 파이썬 클래스다 → 화면 없이 단위 테스트할 수 있다. (TC-05)
모든 계산은 정수로 한다. (NFR-03)
"""
from __future__ import annotations

import random

from common.adapter import (STAGES, STAT_MIN, STAT_MAX, HAPPINESS_MIN, HAPPINESS_MAX,
                            read_player, read_job, read_item, read_event, read_character,
                            meets_requirements, clamp)

# 인생 단계별 기본 투자 비율(여유 자금 중 몇 %) — 게임 끝이 가까울수록 보수적으로
STAGE_INVEST_PERCENT = {"성년기": 50, "중년기": 40, "노년기": 20}


class NPC:
    def __init__(self,
                 money_unit: int = 10_000,      # 점수 1점 = 1만원
                 happiness_weight: int = 10,     # 행복도 1 = 10점
                 stat_weight: int = 2,           # 능력치 1 = 2점 (불행 피해 감소·직업 조건에 도움)
                 min_reserve: int = 500_000,     # 이 금액 이하로는 돈을 쓰지 않는다 (3.4: 일정 금액 이하면 구매 X)
                 reserve_percent: int = 30,      # 보유 자금의 30%는 항상 남겨 둔다
                 laps_per_stage: int = 2,        # 한 인생 단계당 완주 횟수 (Model 규칙과 맞출 것)
                 lead_margin: int = 100,         # 이 점수 이상 앞서면 '이기고 있다'고 판단
                 think_delay_ms: int = 800,      # NPC 차례에 주사위를 굴리기 전 기다리는 시간
                 seed=None):
        self.money_unit = money_unit
        self.happiness_weight = happiness_weight
        self.stat_weight = stat_weight
        self.min_reserve = min_reserve
        self.reserve_percent = reserve_percent
        self.laps_per_stage = laps_per_stage
        self.lead_margin = lead_margin
        self.think_delay_ms = think_delay_ms
        self.rng = random.Random(seed)

    # ════════════════ 1. 점수 계산 (모든 판단의 기준) ════════════════
    def score(self, money: int, happiness: int) -> int:
        return money // self.money_unit + happiness * self.happiness_weight

    def player_score(self, player) -> int:
        info = read_player(player)
        return self.score(info.money, info.happiness)

    def value_of_change(self, player, money: int = 0, happiness: int = 0, stats: dict = None) -> int:
        """변화량(돈·행복도·능력치)이 점수로 몇 점어치인지 계산한다.
        행복도·능력치는 최대/최소를 넘는 부분은 쓸모없으므로 잘라서 계산한다."""
        info = read_player(player)
        value = money // self.money_unit

        new_happy = clamp(info.happiness + happiness, HAPPINESS_MIN, HAPPINESS_MAX)
        value += (new_happy - info.happiness) * self.happiness_weight

        for name, delta in (stats or {}).items():
            now = info.stats.get(name, 0)
            value += (clamp(now + delta, STAT_MIN, STAT_MAX) - now) * self.stat_weight
        return value

    def reserve_money(self, money: int) -> int:
        """항상 남겨 둘 안전 자금"""
        return max(self.min_reserve, money * self.reserve_percent // 100)

    def score_gap(self, player, others) -> int:
        """내 점수 - 다른 플레이어 중 최고 점수 (양수 = 이기는 중)"""
        me = read_player(player)
        rivals = [self.player_score(o) for o in others if read_player(o).id != me.id]
        return self.player_score(me) - max(rivals) if rivals else 0

    def laps_left(self, player) -> int:
        info = read_player(player)
        return max(1, len(STAGES) * self.laps_per_stage - info.lap)

    # ════════════════ 2. 캐릭터 선택 ════════════════
    def choose_character(self, characters, taken_ids):
        """남은 캐릭터 중 능력치 합이 가장 높은 캐릭터 (같으면 무작위)"""
        candidates = [read_character(c) for c in characters]
        candidates = [c for c in candidates if c.id not in taken_ids]
        if not candidates:
            return None
        best = max(sum(c.stats.values()) for c in candidates)
        return self.rng.choice([c for c in candidates if sum(c.stats.values()) == best]).id

    # ════════════════ 3. 직업 선택 (FR-01-12) ════════════════
    def ask_job(self, player, jobs):
        """조건을 만족하는 직업 중 '남은 완주 횟수 × 월급 + 행복도 보너스' 점수가 가장 큰 직업"""
        info = read_player(player)
        eligible = [read_job(j) for j in jobs]
        eligible = [j for j in eligible if meets_requirements(info.stats, j.requirements)]
        if not eligible:
            return None
        laps = self.laps_left(info)

        def value(job):
            return (job.salary * laps) // self.money_unit + self.value_of_change(info, happiness=job.happiness)

        return max(eligible, key=lambda j: (value(j), j.salary)).id

    # ════════════════ 4. 투자 (FR-01-16) ════════════════
    def ask_invest(self, player, others=(), expected_return_percent: int = 10) -> int:
        """투자 금액(정수)을 돌려준다. 0 = 건너뛰기.
          ① 기대 수익이 0 이하이거나 여유 자금이 없으면 투자하지 않는다.
          ② 인생 단계별 기본 비율로 여유 자금의 일부를 투자한다.
          ③ 지고 있으면 +20%p (역전을 노림), 크게 이기고 있으면 -20%p (지키기).
        """
        info = read_player(player)
        if expected_return_percent <= 0:
            return 0
        surplus = info.money - self.reserve_money(info.money)
        if surplus <= 0:
            return 0

        percent = STAGE_INVEST_PERCENT.get(info.stage, 30)
        gap = self.score_gap(info, others)
        if gap < 0:
            percent += 20
        elif gap > self.lead_margin:
            percent -= 20
        percent = clamp(percent, 0, 80)

        amount = surplus * percent // 100
        amount -= amount % self.money_unit          # 1만원 단위로 내림
        return clamp(amount, 0, info.money)

    # ════════════════ 5. 상점 ════════════════
    def ask_shop(self, player, items):
        """안전 자금을 남기고 살 수 있는 아이템 중 '얻는 점수 - 가격'이 가장 큰 것. 이득이 없으면 None"""
        info = read_player(player)
        budget = info.money - self.reserve_money(info.money)
        best_index, best_value = None, 0
        for i, raw in enumerate(items):
            item = read_item(raw)
            if item.price > budget:
                continue
            v = self.value_of_change(info, money=item.money - item.price,
                                     happiness=item.happiness, stats=item.stats)
            if v > best_value:
                best_index, best_value = i, v
        return best_index

    # ════════════════ 6. 선택 이벤트 ════════════════
    def ask_choice(self, player, title: str = "", question: str = "", options=()) -> int:
        """선택지 중 점수 변화가 가장 큰 것의 번호"""
        info = read_player(player)
        values = [self.value_of_change(info, e.money, e.happiness, e.stats)
                  for e in (read_event(o) for o in options)]
        return values.index(max(values)) if values else 0
