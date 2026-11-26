"""
dev_stub/fake_model.py  —  가짜 Model (팀장 데모·테스트용)

왜 있나?  팀원 Model이 완성되기 전에도 View·Input·NPC를 끝까지 돌려 보기 위한 '대역'이다.
         규칙은 게임 규칙 문서를 따르되 많이 간단화했다. 진짜 규칙은 팀원의 model/ 이 맡는다.
간단화한 것 (진짜 Model에서는 규칙 문서대로)
  - 이벤트는 fake_data의 일부만 쓴다. 출산·지갑(선택 이벤트)·복권 세부 규칙 생략
  - 직업 변경권으로 의사는 고를 수 없다 (퇴근 후 재도전 생략)
  - 보관 카드가 3장이면 새 보관 카드는 버린다 (고르기 생략)

FakePlayer의 속성 이름은 계획서 3.3 + 상세 설계 13장 이름이라 common/adapter.py가 그대로 읽는다.
"""
from __future__ import annotations

import random

from common.constants import STAGES, BOARD_SIZE, STAT_MIN, STAT_MAX, BUSINESS_TIERS, STUDIO_SIZE, total_score
from dev_stub import fake_data as D

SIZES = {"조금": 0, "적당히": 1, "많이": 2}
ADULT, MIDDLE, OLD = 2, 3, 4


class FakePlayer:
    def __init__(self, pid: int, name: str, is_npc: bool, character: dict):
        self.player_id = pid
        self.player_name = name
        self.is_npc = is_npc
        self.player_character = character          # dict → 화면에는 이름이 보인다
        self.player_stats = dict(character["stats"])
        self.player_money = D.SETTINGS["start_money"]
        self.player_happiness = D.SETTINGS["start_happiness"]
        self.player_position = 0
        self.player_lap = 0                         # 지금까지 돈 바퀴 수 (누적)
        self.player_age = 0                         # 인생 단계 번호 0~4
        self.player_job = None                      # 직업 dict
        self.job_state = "none"                     # none / student(의대생) / employed
        self.exam_level = 1
        self.shop_type = None                       # 사업가 업종 dict
        self.gig = None                             # 맡은 의뢰 dict 또는 "rest"
        self.gig_double = False
        self.artworks = []
        self.items = []                             # 보관한 황금열쇠 dict (최대 3장)
        self.skip_turns = 0
        self.married = False
        self.children = 0
        self.income_bonus = 0
        self.insurance = False
        self.lecture_pass = False
        self.finished = False
        self.invest_turn = 0                        # 성년기부터 센 자기 턴 수
        self.invested_this_turn = False
        self.investments = []

    @property
    def job_id(self) -> str:
        return self.player_job["id"] if self.player_job else ""


class FakeGame:
    def __init__(self, setup_rows, rng: random.Random = None, quick: bool = False):
        self.rng = rng or random.Random()
        chars = {c["id"]: c for c in D.CHARACTERS}
        self.players = [FakePlayer(i, r["name"], r["is_npc"], chars[r["character_id"]])
                        for i, r in enumerate(setup_rows)]
        laps = D.SETTINGS["quick_laps" if quick else "laps_per_stage"]
        self.stage_ends = [sum(laps[:i + 1]) for i in range(len(laps))]    # [1, 2, 4, 6, 7]
        self.board = list(D.BOARD)
        self.turn_index = 0
        self.round = 1
        self.companies = [dict(c) for c in D.COMPANIES]
        self.key_deck = []
        self.used_questions, self.used_titles = set(), set()
        self.trend, self.trend_rounds_left, self.nft_name = None, 0, D.NFT_NAMES[0]
        self.opening_news = self._pick_trend()

    # ── 차례 ────────────────────────────────────────────────────
    def current_player(self) -> FakePlayer:
        return self.players[self.turn_index]

    def roll_dice(self) -> tuple:
        return self.rng.randint(1, 6), self.rng.randint(1, 6)

    def next_turn(self) -> list:
        """다음 사람으로 넘긴다. 라운드가 바뀌어 유행이 바뀌면 속보 문구 목록을 돌려준다."""
        news = []
        if self.is_over():
            return news
        old = self.turn_index
        i = old
        while True:
            i = (i + 1) % len(self.players)
            if not self.players[i].finished:
                break
        if i <= old:                                  # 한 바퀴 돌았다 = 라운드 끝
            self.round += 1
            self.trend_rounds_left -= 1
            if self.trend_rounds_left <= 0:
                ending = self._headline(self.trend, 1)
                news += [ending] if ending else []
                news.append(self._pick_trend())
        self.turn_index = i
        return news

    def start_turn(self, p: FakePlayer) -> None:
        p.invested_this_turn = False
        if p.player_age >= ADULT:
            p.invest_turn += 1

    def is_over(self) -> bool:
        return all(p.finished for p in self.players)

    # ── 이동과 인생 단계 ─────────────────────────────────────────
    def stage_of_lap(self, lap: int) -> int:
        for i, end in enumerate(self.stage_ends):
            if lap < end:
                return i
        return len(STAGES)                            # 노년기까지 마침

    def move(self, p: FakePlayer, steps: int) -> dict:
        old = p.player_position
        p.player_position = (old + steps) % BOARD_SIZE
        result = {"from": old, "steps": steps, "passed_start": old + steps >= BOARD_SIZE,
                  "old_stage": p.player_age, "new_stage": p.player_age}
        if result["passed_start"]:
            p.player_lap += 1
            stage = self.stage_of_lap(p.player_lap)
            if stage >= len(STAGES):
                p.finished = True
            else:
                p.player_age = result["new_stage"] = stage
        return result

    # ── 수치 도우미 ─────────────────────────────────────────────
    def _value(self, stage_name: str, key: str, word: str) -> tuple:
        """'+적당히' → (그 단계 숫자, '적당히')"""
        size = word.strip("+-")
        table = D.SCALE[stage_name]["money" if key == "money" else "happiness" if key == "happiness" else "stat"]
        return (-1 if word.startswith("-") else 1) * table[SIZES[size]], size

    def _gain(self, p: FakePlayer, money: int = 0, happiness: int = 0, stats: dict = None) -> tuple:
        """돈·행복·능력치를 더한다 (캐릭터 특성 적용). 실제로 더한 값을 돌려준다."""
        cid = p.player_character["id"]
        if happiness > 0 and cid == "dreamer":
            happiness = happiness * 11 // 10
        p.player_money += money
        p.player_happiness += happiness
        applied = {}
        for stat, v in (stats or {}).items():
            if v > 0 and stat == "지력" and cid == "scholar":
                v = v * 3 // 2
            before = p.player_stats[stat]
            p.player_stats[stat] = max(STAT_MIN, min(STAT_MAX, before + v))
            applied[stat] = p.player_stats[stat] - before
        return money, happiness, applied

    def _reduce(self, p: FakePlayer, value: int, stat_value: int, use_insurance: bool) -> int:
        if value >= 0:
            return value
        damage = -value * (200 - stat_value) // 200
        if p.player_character["id"] == "athlete":
            damage = damage * 80 // 100
        if use_insurance:
            damage = damage * 50 // 100
        return -damage

    # ── 행운·불행 ───────────────────────────────────────────────
    def draw_event(self, p: FakePlayer, kind: str) -> dict:
        stage = STAGES[p.player_age]
        if p.job_state == "student":
            pool = [e for e in D.EVENTS if e["stage"] == "청년기" and e.get("job") in (None, "student")]
        elif p.player_age in (ADULT, MIDDLE):
            pool = [e for e in D.EVENTS if e["stage"] == stage and e.get("job") in (p.job_id, "common")]
            pool = pool or [e for e in D.EVENTS if e.get("job") in (p.job_id, "common")]
        else:
            pool = [e for e in D.EVENTS if e["stage"] == stage and not e.get("job")]
        return self.rng.choice([e for e in pool if e["kind"] == kind])

    def event_stage(self, p: FakePlayer) -> str:
        return "청년기" if p.job_state == "student" else STAGES[p.player_age]

    def preview(self, p: FakePlayer, template: dict) -> dict:
        """적용하기 전 이벤트 정보 (NPC가 '피해 크기'로 판단할 때)"""
        sizes = [w.strip("+-") for w in template["effects"].values()]
        size = max(sizes, key=lambda s: SIZES[s]) if sizes else ""
        return {"kind": template["kind"], "name": template["name"], "size": size}

    def apply_event(self, p: FakePlayer, template: dict, multiplier: int = 1) -> dict:
        stage = self.event_stage(p)
        money = happiness = 0
        stats = {}
        for key, word in template["effects"].items():
            value = self._value(stage, key, word)[0] * multiplier
            if key == "money":
                money += value
            elif key == "happiness":
                happiness += value
            else:
                stats[key] = value
        event = {"kind": template["kind"], "name": template["name"], "description": template.get("text", ""),
                 "stage_label": stage + (f" · {p.player_job['name']}" if p.player_job and p.player_age in (ADULT, MIDDLE) else ""),
                 "size": self.preview(p, template)["size"], "lines": []}
        if multiplier > 1:
            event["lines"].append("황금열쇠 '행운 보상 2배' 적용!")
        if template["kind"] == "badluck" and (money < 0 or happiness < 0):
            stat = template.get("stat", "")
            sv = p.player_stats.get(stat, 0)
            use_insurance = p.insurance
            p.insurance = False
            base = -money + -happiness * 10
            money2 = self._reduce(p, money, sv, use_insurance)
            happiness2 = self._reduce(p, happiness, sv, use_insurance)
            after = -money2 + -happiness2 * 10
            event.update(base_money=money, base_happiness=happiness, reduce_stat=stat, reduce_value=sv,
                         reduce_percent=100 - after * 100 // base if base else 0)
            if use_insurance:
                event["lines"].append("보험 덕분에 피해가 절반으로 줄었다.")
            money, happiness = money2, happiness2
        money, happiness, stats = self._gain(p, money, happiness, stats)
        event.update(money=money, happiness=happiness, stats=stats)
        special = template.get("special")
        if special == "marry":
            if p.married:
                event["lines"].append("이미 결혼했다. 결혼기념일 여행을 다녀왔다.")
            p.married = True
            event["lines"].append("지속 효과: 매 턴 행복 +5")
        elif special == "promote" and p.income_bonus < 2:
            p.income_bonus += 1
            event["lines"].append(f"매 턴 수입 +10% (승진 {p.income_bonus}/2)")
        if template.get("skip_turns"):
            p.skip_turns += template["skip_turns"]
            event["skip_turns"] = template["skip_turns"]
        return event

    # ── 황금열쇠 ────────────────────────────────────────────────
    def card(self, p: FakePlayer, card_id: str):
        return next((c for c in p.items if c["id"] == card_id), None)

    def take_card(self, p: FakePlayer, card_id: str) -> bool:
        c = self.card(p, card_id)
        if c:
            p.items.remove(c)
        return c is not None

    def draw_golden_key(self, p: FakePlayer) -> dict:
        if not self.key_deck:
            self.key_deck = [dict(c) for c in D.GOLDEN_KEYS for _ in range(c["count"])]
            self.rng.shuffle(self.key_deck)
        card = self.key_deck.pop()
        event = {"kind": "golden_key", "name": card["name"], "description": card["description"], "lines": []}
        if card["id"] == "lottery":
            d1, d2 = self.roll_dice()
            event["lines"].append(f"복권 주사위 {d1} + {d2} = {d1 + d2}")
            if d1 + d2 >= 10:
                money = self._value(STAGES[p.player_age], "money", "+많이")[0]
                event["money"] = self._gain(p, money)[0]
                event["lines"].append("당첨!")
            else:
                event["lines"].append("꽝... 종이 한 장이 남았다.")
        elif card["keep"]:
            if len(p.items) < 3:
                p.items.append(card)
                event["lines"].append("보관함에 넣었다. (최대 3장)")
            else:
                event["lines"].append("보관함이 꽉 차서 버렸다.")
        return event

    # ── 상점 ────────────────────────────────────────────────────
    def shop_items(self, p: FakePlayer) -> list:
        scale = D.SCALE[STAGES[p.player_age]]
        items = []
        for it in D.SHOP:
            if it.get("student_only") and p.job_state != "student":
                continue
            item = {"id": it["id"], "name": it["name"], "price": scale["money"][SIZES[it["price"]]],
                    "description": it.get("description", "")}
            if "stat" in it:
                item["stats"] = {it["stat"]: scale["stat"][SIZES[it["amount"]]]}
            items.append(item)
        return items

    def buy(self, p: FakePlayer, item: dict) -> dict:
        p.player_money -= item["price"]
        if item["id"] == "insurance":
            p.insurance = True
        if item["id"] == "lecture_pass":
            p.lecture_pass = True
        stats = self._gain(p, 0, 0, item.get("stats"))[2]
        return {"kind": "info", "name": f"{item['name']} 구매", "money": -item["price"], "stats": stats,
                "description": item.get("description", "")}

    # ── 직업 ────────────────────────────────────────────────────
    def jobs_for(self, p: FakePlayer) -> list:
        """평범이는 직업 조건이 10씩 낮다 (화면에도 줄어든 조건을 보여 준다)"""
        cut = 10 if p.player_character["id"] == "normal" else 0
        return [dict(j, requirements={k: max(0, v - cut) for k, v in j["requirements"].items()}) for j in D.JOBS]

    def find_job(self, job_id: str) -> dict:
        return next(j for j in D.JOBS if j["id"] == job_id)

    def set_job(self, p: FakePlayer, job_id: str) -> dict:
        self._leave_job(p)
        job = self.find_job(job_id)
        if job["device"] == "exam":
            p.job_state, p.player_job, p.exam_level = "student", None, 1
            return {"kind": "exam", "name": "의대생이 됐다!", "description": "다음 턴부터 주사위를 굴릴 때마다 국가고시를 본다."}
        p.job_state, p.player_job = "employed", job
        return {"kind": "info", "name": f"{job['name']}(이)가 됐다!", "description": job["description"]}

    def _leave_job(self, p: FakePlayer) -> None:
        """직업을 바꾸면 맡은 의뢰는 정산하고, 작업실 작품은 판매가에 판다 (간단화: 돈만)"""
        if p.job_id == "freelancer" and isinstance(p.gig, dict):
            p.player_money += p.gig["pay"]
        p.gig = None
        if p.artworks:
            p.player_money += sum(a["price"] for a in p.artworks)
            p.artworks = []
        p.shop_type = None

    # ── 의사 국가고시 ───────────────────────────────────────────
    def exam_question(self, p: FakePlayer) -> dict:
        level = [q for q in D.EXAM if q["level"] == p.exam_level]
        pool = [q for q in level if q["id"] not in self.used_questions] or level   # 다 쓰면 다시 섞는다
        q = self.rng.choice(pool)
        self.used_questions.add(q["id"])
        return q

    def exam_time_limit(self, p: FakePlayer) -> int:
        return 10 + p.player_stats["지력"] // 10 + (10 if p.lecture_pass else 0)

    def grade_exam(self, p: FakePlayer, question: dict, answer) -> dict:
        p.lecture_pass = False
        if answer == question["answer"]:
            reward = self._value("성년기", "happiness", "+많이" if p.exam_level == 1 else "+조금")[0]
            happiness = self._gain(p, 0, reward)[1]
            p.job_state, p.player_job = "employed", self.find_job("doctor")
            text = "한 번에 합격! 부모님이 동네에 현수막을 거셨다." if p.exam_level == 1 else "N수 끝에 드디어 흰 가운을 입었다."
            return {"kind": "luck", "name": "국가고시 합격!", "description": text, "happiness": happiness, "passed": True}
        text = "시간 초과! 내년을 기약하자..." if answer is None else f"정답은 {question['answer']}번이었다."
        return {"kind": "badluck", "name": f"{p.exam_level}단계 불합격", "description": text, "passed": False}

    def retry_exam(self, p: FakePlayer) -> bool:
        """재수: 다음 단계로. 5단계에서 떨어지면 False (불합격 확정)"""
        if p.exam_level >= 5:
            p.job_state = "none"
            return False
        p.exam_level += 1
        return True

    def give_up_exam(self, p: FakePlayer) -> None:
        p.job_state, p.player_job = "none", None

    # ── 사업가 ──────────────────────────────────────────────────
    def business_id(self, p: FakePlayer):
        return p.shop_type["id"] if p.shop_type else None

    def set_business(self, p: FakePlayer, business_id: str, cost: int = 0) -> None:
        p.player_money -= cost
        p.shop_type = next(b for b in D.BUSINESSES if b["id"] == business_id)

    def business_result(self, p: FakePlayer, dice_sum: int, use_trend: bool = True) -> dict:
        b = p.shop_type
        bonus = (b["trend_bonus"] if self.trend == b["id"] else b["off_trend"]) if use_trend else 0
        total = dice_sum + bonus
        tier = 0 if total <= 4 else 1 if total <= 8 else 2 if total <= 11 else 3
        money, happiness = b["table"][tier]
        sign = f" {'+' if bonus > 0 else '-'} {abs(bonus)}" if bonus else ""
        return {"kind": "business", "name": f"{b['name']} 실적: {BUSINESS_TIERS[tier]}",
                "description": f"주사위 합 {dice_sum}{sign} = {total}", "money": money, "happiness": happiness}

    def _pick_trend(self) -> str:
        self.trend = self.rng.choice(["store", "youtube", "nft", None])
        self.trend_rounds_left = D.SETTINGS["trend_rounds"]
        self.nft_name = self.rng.choice(D.NFT_NAMES)
        return self._headline(self.trend, 0)

    def _headline(self, trend, which: int) -> str:
        return D.TREND_HEADLINES[trend or "none"][which].format(nft=self.nft_name)

    def trend_label(self) -> str:
        name = next((b["name"] for b in D.BUSINESSES if b["id"] == self.trend), None)
        if name is None:
            return f"지금은 유행이 없어요 ({self.trend_rounds_left}라운드 남음)"
        return f"지금 유행: {name} ({self.trend_rounds_left}라운드 남음)"

    # ── 프리랜서 ────────────────────────────────────────────────
    def gig_cards(self) -> list:
        return self.rng.sample(D.GIGS, 3)          # 펼친 3장은 매번 다시 섞어 넣는다

    def take_gig(self, p: FakePlayer, gig_id) -> None:
        p.gig = next((g for g in D.GIGS if g["id"] == gig_id), "rest")

    def settle_gig(self, p: FakePlayer) -> dict:
        gig, p.gig = p.gig, None
        if gig in (None, "rest"):
            happiness = self._gain(p, 0, D.SETTINGS["rest_happiness"])[1]
            return {"kind": "gig", "name": "한 바퀴 안식월", "description": "푹 쉬었다.", "happiness": happiness}
        pay = gig["pay"] * (2 if p.gig_double else 1)
        p.gig_double = False
        money, happiness = pay, gig.get("happiness", 0)
        d1, d2 = self.roll_dice()
        lines = [f"보수 {pay:,}만원" + (" (입소문 2배!)" if pay != gig["pay"] else ""), f"정산 주사위 {d1} + {d2} = {d1 + d2}"]
        if gig.get("risk") and gig["risk"][0] <= d1 + d2 <= gig["risk"][1]:
            acc = gig["accident"]
            sv = p.player_stats.get(gig["stat"], 0)
            money += self._reduce(p, acc.get("money", 0), sv, False)
            happiness += self._reduce(p, acc.get("happiness", 0), sv, False)
            lines.append(f"사고: {acc['text']} ({gig['stat']} {sv}로 피해 감소)")
        if gig.get("jackpot") and gig["jackpot"][0] <= d1 + d2 <= gig["jackpot"][1]:
            bonus = gig["bonus"]
            money += bonus.get("money", 0)
            p.gig_double = bool(bonus.get("double_next"))
            lines.append(f"대박: {bonus['text']}")
        money, happiness, stats = self._gain(p, money, happiness, gig.get("stats"))
        return {"kind": "gig", "name": f"의뢰 정산: {gig['name']}", "money": money, "happiness": happiness,
                "stats": stats, "lines": lines}

    # ── 예술가 ──────────────────────────────────────────────────
    def make_artwork(self, p: FakePlayer) -> dict:
        d1, d2 = self.roll_dice()
        score = d1 + d2 + p.player_stats["센스"] // 20
        grade = [g for g in D.ART["grades"] if score >= g["min"]][-1]
        titles = [t for t in D.ART["titles"] if t not in self.used_titles] or D.ART["titles"]
        title = self.rng.choice(titles)
        self.used_titles.add(title)
        return {"id": f"art-{p.player_id}-{len(self.used_titles)}-{self.rng.randint(100, 999)}", "title": title,
                "grade": grade["name"], "price": grade["price"], "text": grade["text"], "score": score}

    def place_artwork(self, p: FakePlayer, artwork: dict, sell_id) -> dict:
        everything = p.artworks + [artwork]
        sold = next((a for a in everything if a["id"] == sell_id), None)
        p.artworks = [a for a in everything if a is not sold][:STUDIO_SIZE]
        if sold is None:
            return {"kind": "artwork", "name": f"'{artwork['title']}' 보관", "description": "작업실에 걸어 두었다."}
        money = self._gain(p, sold["price"])[0]
        return {"kind": "artwork", "name": f"'{sold['title']}' 판매", "description": f"{sold['grade']} 작품을 팔았다.", "money": money}

    def retrospective(self, p: FakePlayer) -> dict:
        works, p.artworks = p.artworks, []
        money = self._gain(p, sum(a["price"] * 2 for a in works))[0]
        return {"kind": "artwork", "name": "회고전 개최!", "description": "작가가 은퇴하자 재평가됐다.",
                "money": money, "lines": [f"'{a['title']}' {a['grade']} → {a['price'] * 2:,}만원" for a in works]}

    # ── 매 턴 수입 ──────────────────────────────────────────────
    def apply_income(self, p: FakePlayer, steps: int, dice_sum: int) -> dict:
        result = {"money": 0, "happiness": 0, "event": None}
        if p.job_state != "employed" or not p.player_job:
            return result
        job, old = p.player_job, p.player_age == OLD
        if job["device"] == "business" and p.shop_type:
            event = self.business_result(p, dice_sum, use_trend=not old)
            money, happiness = event["money"], event["happiness"]
            if old:
                money, happiness = money * 50 // 100, happiness * 50 // 100
                event["lines"] = ["연금: 실적의 50%"]
            result["event"] = event
        else:
            income = job.get("pension_income", job["income"]) if old else job["income"]
            money, happiness = income["money"] * steps, income["happiness"] * steps
            if old:
                money, happiness = money * job["pension"] // 100, happiness * job["pension"] // 100
        money = money * (100 + 10 * p.income_bonus) // 100
        happiness += 5 if p.married else 0
        money, happiness, _ = self._gain(p, money, happiness)
        result.update(money=money, happiness=happiness)
        return result

    # ── 투자와 회사 ─────────────────────────────────────────────
    def invest_ready(self, p: FakePlayer) -> bool:
        return (p.player_age >= ADULT and p.invest_turn % D.SETTINGS["invest_every"] == 1
                and not p.invested_this_turn and p.player_money > 0)

    def invest(self, p: FakePlayer, company_id: str, amount: int) -> dict:
        c = next(c for c in self.companies if c["id"] == company_id)
        p.player_money -= amount
        p.invested_this_turn = True
        p.investments.append({"company": c, "amount": amount, "turns_left": D.SETTINGS["invest_wait"]})
        return {"kind": "invest", "name": f"{c['name']}에 투자", "money": -amount,
                "description": f"{D.SETTINGS['invest_wait']}턴 뒤에 결과가 나온다."}

    def settle_investments(self, p: FakePlayer) -> list:
        events = []
        for inv in list(p.investments):
            inv["turns_left"] -= 1
            if inv["turns_left"] > 0:
                continue
            p.investments.remove(inv)
            c = inv["company"]
            d1, d2 = self.roll_dice()
            bucket = [3, 5, 8, 10, 12].index(next(x for x in [3, 5, 8, 10, 12] if d1 + d2 <= x))
            ratio = c["ratios_x10"][bucket] + (5 if self.take_card(p, "invest_up") else 0)
            back = inv["amount"] * ratio // 10
            mood = self._value(STAGES[p.player_age], "happiness", "+조금" if back >= inv["amount"] else "-조금")[0]
            money, happiness, _ = self._gain(p, back, mood)
            events.append({"kind": "invest", "name": f"{c['name']} 투자 결과", "money": money, "happiness": happiness,
                           "lines": [f"주사위 {d1} + {d2} = {d1 + d2} → ×{ratio / 10:g}",
                                     f"{inv['amount']:,}만원 → {back:,}만원"]})
        return events

    # ── 게임 끝 ────────────────────────────────────────────────
    def finish(self) -> None:
        """정산 안 된 투자는 원금만 돌려준다"""
        for p in self.players:
            for inv in p.investments:
                p.player_money += inv["amount"]
            p.investments = []

    def ranking(self) -> list:
        rows = [{"name": p.player_name, "job": p.player_job["name"] if p.player_job else "-",
                 "money": p.player_money, "happiness": p.player_happiness,
                 "score": total_score(p.player_money, p.player_happiness),
                 "character": p.player_character["name"], "is_npc": p.is_npc} for p in self.players]
        return sorted(rows, key=lambda r: (r["score"], r["money"]), reverse=True)
