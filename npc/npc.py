"""
npc/npc.py  —  NPC: 컴퓨터 플레이어의 판단 (FR-01-19 · 게임 규칙 문서 'NPC 판단 규칙')

핵심 아이디어
  모든 선택지를 '기대 점수 = 돈(만원) + 행복 × 10'으로 바꿔서 비교하고, 가장 큰 것을 고른다.
  순위가 낮을수록 위험한 선택을 더 한다 (투자 유형).

사용법 — 사람(Input)과 NPC는 함수 이름·인자·반환값이 같다.
    decider = npc if player.is_npc else input_handler
    job_id = decider.ask_job(player, jobs)
  그래서 Controller는 "누가 고르는지"를 신경 쓰지 않아도 된다.

지켜야 할 것
  - Qt를 쓰지 않는 순수 파이썬이다 → 화면 없이 테스트할 수 있다.
  - 기다리는 연출은 Controller가 QTimer.singleShot(npc.think_delay_ms(), ...)로 한다. time.sleep 금지.
  - 게임 규칙(실적 계산, 피해 계산 등)을 '바꾸지' 않는다. 규칙을 '예상'하는 데만 쓴다.
  - rng를 넘겨주면 결과가 항상 같아서 테스트하기 쉽다.
"""
from __future__ import annotations

import random

from common.constants import STAGES, STUDIO_SIZE, total_score, HAPPINESS_WEIGHT
from common.adapter import (read_player, read_job, read_item, read_company, read_business, read_gig,
                            read_artwork, read_question, read_event, read_card, read_character,
                            meets_requirements, stage_index, pick)

# ── 판단에 쓰는 숫자 (규칙 문서 'NPC 판단 규칙'과 같게) ─────────────
WORK_TURNS = 16                # 성년기·중년기에 일하는 턴 수 (약 16)
PENSION_TURNS = 4              # 노년기 턴 수 (약 4)
AVG_MOVE = 7                   # 주사위 2개 합 평균
EMERGENCY_FUND = 500           # 비상금 500만원: 이만큼은 남겨 둔다
INVEST_RATIO = 50              # 투자 금액 = (보유 자금 - 비상금)의 50%
SWITCH_MONEY = 2000            # 업종 바꾸기: 2,000만원 이상 있을 때만
SWITCH_ROUNDS = 2              # 업종 바꾸기: 유행이 2라운드 이상 남았을 때만
DEFAULT_BUSINESS = "youtube"   # 유행이 없을 때 고르는 업종
EXAM_BASE = [30, 45, 60, 75, 90]   # 국가고시 단계별 기본 합격 확률(%) 1→5
EXAM_MIN, EXAM_MAX = 5, 95
DOCTOR_TURN_VALUE = 770        # 재수 1턴마다 잃는 의사 수입 (700만원 + 행복 7×10)
DOUBLE_NEXT_VALUE = 900        # '다음 의뢰 보수 2배' 대박의 가치 (의뢰 보수 평균쯤)
THINK_MS = (800, 1200)         # 고민하는 척 기다리는 시간
STAGE_ADULT = STAGES.index("성년기")


def dice_ways(low: int, high: int) -> int:
    """주사위 2개 합이 low~high인 경우의 수 (36가지 중)"""
    return sum(1 for a in range(1, 7) for b in range(1, 7) if low <= a + b <= high)


def reduced_damage(points: int, stat_value: int) -> int:
    """규칙 문서 '불행 피해 감소' 공식: 피해 × (200 - 능력치) ÷ 200"""
    return points * (200 - stat_value) // 200


def exam_pass_chance_x10(level: int, intellect: int) -> int:
    """NPC 국가고시 합격 확률 × 10 (정수). 예) 지력 60, 1단계 → 300 = 30.0%"""
    level = min(max(level, 1), 5)
    chance = EXAM_BASE[level - 1] * 10 + (intellect - 60) * 5      # (지력 - 60) × 0.5%p
    return min(max(chance, EXAM_MIN * 10), EXAM_MAX * 10)


def expected_retakes_x1000(intellect: int, start_level: int = 1) -> int:
    """평균 재수 턴 × 1000. 지력 60이면 약 1280 (= 1.28턴)"""
    fail, total = 1000, 0
    for level in range(start_level, 6):
        fail = fail * (1000 - exam_pass_chance_x10(level, intellect)) // 1000
        total += fail
    return total


def job_turn_value(job) -> int:
    """직업의 매 턴 기대 점수. 데이터에 expected_value가 없으면 칸당 수입 × 평균 이동(7칸)"""
    j = read_job(job)
    return j.expected_value or (j.income_money + j.income_happiness * HAPPINESS_WEIGHT) * AVG_MOVE


def job_value(job, intellect: int = 60) -> int:
    """직업 선택 점수 = 매 턴 기대 점수 × 16 + 연금(매 턴 기대 점수 × 4 × 연금 비율)
    의사는 '평균 재수 턴 × 770'을 뺀다."""
    j = read_job(job)
    per_turn = job_turn_value(j)
    value = per_turn * WORK_TURNS + per_turn * PENSION_TURNS * j.pension // 100
    if j.device == "exam" or j.id == "doctor":
        value -= expected_retakes_x1000(intellect) * DOCTOR_TURN_VALUE // 1000
    return value


def gig_value(card, stats: dict) -> int:
    """의뢰 카드 기대 점수 = 보수 + 행복 × 10 - 사고 확률 × 줄어든 피해 + 대박 확률 × 대박 가치"""
    g = read_gig(card)
    value = g.pay + g.happiness * HAPPINESS_WEIGHT
    if g.risk:
        damage = abs(int(g.accident.get("money", 0))) + abs(int(g.accident.get("happiness", 0))) * HAPPINESS_WEIGHT
        value -= dice_ways(*g.risk) * reduced_damage(damage, stats.get(g.stat, 0)) // 36
    if g.jackpot:
        bonus = int(g.bonus.get("money", 0)) + int(g.bonus.get("happiness", 0)) * HAPPINESS_WEIGHT
        if g.bonus.get("double_next"):
            bonus += DOUBLE_NEXT_VALUE
        value += dice_ways(*g.jackpot) * bonus // 36
    return value


def rank_of(player, players) -> tuple:
    """(순위, 인원) — 총점이 나보다 높은 사람 수 + 1"""
    me = read_player(player)
    infos = [read_player(p) for p in players] or [me]
    if all(p.id != me.id for p in infos):
        infos.append(me)
    my_score = total_score(me.money, me.happiness)
    rank = 1 + sum(1 for p in infos if p.id != me.id and total_score(p.money, p.happiness) > my_score)
    return rank, len(infos)


class NPC:
    def __init__(self, rng: random.Random = None):
        self.rng = rng or random.Random()

    # ── 연출 ────────────────────────────────────────────────────
    def think_delay_ms(self) -> int:
        """행동하기 전 기다릴 시간(ms). Controller가 QTimer.singleShot에 넣는다."""
        return self.rng.randint(*THINK_MS)

    # ── 게임 준비 ───────────────────────────────────────────────
    def choose_character(self, characters, taken_ids=()):
        """남은 캐릭터 중 하나를 무작위로 고른다."""
        free = [read_character(c).id for c in characters if read_character(c).id not in set(taken_ids)]
        return self.rng.choice(free) if free else None

    # ── 직업 ────────────────────────────────────────────────────
    def ask_job(self, player, jobs, exclude=(), allow_keep: bool = False, heading: str = ""):
        """조건이 되는 직업 중 job_value가 가장 큰 것. allow_keep이면 지금보다 나을 때만 바꾼다(아니면 None)."""
        info = read_player(player)
        intellect = info.stats.get("지력", 0)
        candidates = [read_job(j) for j in jobs]
        able = [j for j in candidates if j.id not in set(exclude) and meets_requirements(info.stats, j.requirements)]
        if not able:
            return None if allow_keep else (candidates[-1].id if candidates else None)
        best = max(able, key=lambda j: job_value(j, intellect))
        if allow_keep:
            current = next((j for j in candidates if info.job in (j.id, j.name)), None)
            if current is not None and job_value(current, intellect) >= job_value(best, intellect):
                return None
            if current is not None and best.id == current.id:
                return None
        return best.id

    def ask_exam_answer(self, player, question, time_limit: int = 0, level_name: str = ""):
        """문제를 풀지 않고 확률로 맞힌다. 맞히면 정답 번호, 틀리면 다른 번호 (시간 초과는 없음)"""
        info = read_player(player)
        q = read_question(question)
        answer = q.answer if 1 <= q.answer <= 4 else 1
        if self.rng.randrange(1000) < exam_pass_chance_x10(q.level, info.stats.get("지력", 0)):
            return answer
        return self.rng.choice([n for n in (1, 2, 3, 4) if n != answer])

    def ask_retry_exam(self, player, level: int) -> bool:
        """NPC는 포기하지 않고 5단계까지 본다."""
        return True

    # ── 사업가 ──────────────────────────────────────────────────
    def ask_business(self, player, businesses, trend=None, rounds_left: int = 0):
        """처음 업종: 지금 유행 업종, 유행이 없으면 유튜브 채널"""
        ids = [read_business(b).id for b in businesses]
        if trend in ids:
            return trend
        return DEFAULT_BUSINESS if DEFAULT_BUSINESS in ids else (ids[0] if ids else None)

    def ask_switch_business(self, player, businesses, current=None, trend=None, rounds_left: int = 0,
                            cost: int = 1000):
        """유행 업종이 내 업종과 다르고, 2라운드 이상 남았고, 돈이 2,000만원 이상이면 바꾼다."""
        info = read_player(player)
        ids = [read_business(b).id for b in businesses]
        if (trend in ids and trend != current and rounds_left >= SWITCH_ROUNDS
                and info.money >= max(SWITCH_MONEY, cost)):
            return trend
        return None

    # ── 프리랜서 · 예술가 ─────────────────────────────────────────
    def ask_gig(self, player, cards, rest_happiness: int = 50):
        """기대 점수가 가장 큰 의뢰. 쉬기(행복 50 = 500점)보다 작으면 쉰다(None)."""
        info = read_player(player)
        if not cards:
            return None
        best = max(cards, key=lambda c: gig_value(c, info.stats))
        if gig_value(best, info.stats) < rest_happiness * HAPPINESS_WEIGHT:
            return None
        return read_gig(best).id

    def ask_artwork(self, player, artwork, studio, studio_size: int = STUDIO_SIZE):
        """언제나 보관한다. 작업실이 넘치면 판매가가 가장 싼 작품을 판다."""
        studio = [read_artwork(a) for a in (studio or [])]
        if len(studio) < studio_size:
            return None
        everything = studio + [read_artwork(artwork)]
        return min(everything, key=lambda a: a.price).id

    # ── 돈 쓰기 ─────────────────────────────────────────────────
    def ask_shop(self, player, items, jobs=()):
        """직업 전: 목표 직업에 모자란 능력치를 산다. 직업 후: 비상금이 남을 때만 보험.
        items의 price는 그 단계 가격(Model이 계산해서 넘김). 반환: 상품 번호 / None"""
        info = read_player(player)
        goods = [read_item(i) for i in items]
        affordable = [(n, g) for n, g in enumerate(goods) if g.price <= info.money]
        if info.job_state == "none" and stage_index(info.stage) < STAGE_ADULT and jobs:
            target = max((read_job(j) for j in jobs), key=lambda j: job_value(j, info.stats.get("지력", 0)))
            missing = {s: v - info.stats.get(s, 0) for s, v in target.requirements.items() if v > info.stats.get(s, 0)}
            if not missing:
                return None
            need = max(missing, key=missing.get)               # 가장 많이 모자란 능력치
            for n, g in affordable:
                if g.stats.get(need, 0) > 0:
                    return n
            return None
        if info.insurance:
            return None
        for n, g in affordable:
            if (g.id == "insurance" or "보험" in g.name) and info.money - g.price >= EMERGENCY_FUND:
                return n
        return None

    def ask_invest(self, player, companies, others=()):
        """1위면 안정형, 꼴찌면 도박형, 그 사이는 성장형 회사에 투자한다.
        금액 = (보유 자금 - 비상금)의 50%, 10만원 단위로 내림. 반환: {"company_id", "amount"} / None"""
        info = read_player(player)
        amount = (info.money - EMERGENCY_FUND) * INVEST_RATIO // 100 // 10 * 10
        infos = [read_company(c) for c in companies]
        if amount <= 0 or not infos:
            return None
        rank, count = rank_of(info, others)
        wanted = "stable" if rank == 1 else "gamble" if rank == count else "growth"
        same_type = [c for c in infos if c.type == wanted]
        choice = max(same_type or infos, key=lambda c: c.expected_x100)
        return {"company_id": choice.id, "amount": amount}

    # ── 이벤트 ──────────────────────────────────────────────────
    def ask_choice(self, player, title: str, question: str, options):
        """선택지에 돈·행복 숫자가 있으면 점수가 큰 것, 없으면 첫 번째"""
        def score(option):
            return int(pick(option, ("money",), 0) or 0) + int(pick(option, ("happiness",), 0) or 0) * HAPPINESS_WEIGHT
        if not options:
            return 0
        scores = [score(o) if not isinstance(o, str) else 0 for o in options]
        return scores.index(max(scores))

    def ask_use_card(self, player, card, event=None) -> bool:
        """불운→행운 변경권: 피해가 '적당히' 이상일 때만 쓴다. 그 밖의 카드는 쓴다."""
        c = read_card(card)
        if c.id == "bad_to_good" or "불운" in c.name:
            return event is not None and read_event(event).size in ("적당히", "많이")
        return True
