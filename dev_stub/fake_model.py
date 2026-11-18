"""
dev_stub/fake_model.py  —  ⚠ 임시 코드 (팀원 Model이 오기 전 테스트용)

팀원의 Model(Player, Board, Tile, Dice)이 완성되기 전에
내 View·Input·NPC가 제대로 동작하는지 돌려 보려고 만든 "가짜 Model"이다.
  - 속성 이름은 계획서 3.3 자료구조(player_money 등)를 따랐다.
  - 캐릭터·직업·이벤트 수치는 화면 확인용 예시일 뿐, 실제 값은 팀원 Model과 JSON이 정한다.
  - 팀원 코드로 바꾸면 이 폴더(dev_stub)는 통째로 지워도 된다.
"""
from __future__ import annotations

import random

from common.adapter import BOARD_SIZE, STAGES, STAT_MIN, STAT_MAX, HAPPINESS_MIN, HAPPINESS_MAX, clamp

LAPS_PER_STAGE = 1          # 데모를 빨리 보려고 1바퀴마다 단계 상승 (실제 값은 Model이 정함)
START_MONEY = 3_000_000
START_HAPPINESS = 50
BASE_SALARY = 200_000       # 직업이 없을 때 출발 칸 통과 보너스
INVEST_EVERY = 5            # 성년기 이후 5턴마다 투자 기회

CHARACTERS = [
    {"id": "student", "name": "모범생", "stats": {"지력": 70, "체력": 40, "센스": 50},
     "trait": "지력이 오르는 이벤트 효과 +20%"},
    {"id": "athlete", "name": "운동선수", "stats": {"지력": 40, "체력": 75, "센스": 45},
     "trait": "불행 칸 피해 -20%"},
    {"id": "artist", "name": "예술가", "stats": {"지력": 45, "체력": 40, "센스": 75},
     "trait": "행복도 획득 +20%"},
    {"id": "merchant", "name": "사업가", "stats": {"지력": 55, "체력": 50, "센스": 55},
     "trait": "투자 수익 +10%"},
]

JOBS = [
    {"id": "doctor", "name": "의사", "salary": 900_000, "requirements": {"지력": 72}},
    {"id": "pro", "name": "프로 선수", "salary": 700_000, "requirements": {"체력": 72}},
    {"id": "designer", "name": "디자이너", "salary": 600_000, "requirements": {"센스": 70}, "happiness": 5},
    {"id": "office", "name": "회사원", "salary": 500_000, "requirements": {"지력": 50}},
    {"id": "parttime", "name": "아르바이트", "salary": 300_000, "requirements": {}},
]

# 인생 단계별 이벤트 (FR-01-14, 15). "stat"은 불행 피해를 줄여 주는 관련 능력치
LUCK_EVENTS = {
    "유아기": [{"name": "첫 걸음마", "description": "온 가족이 기뻐했다.", "happiness": 10},
              {"name": "그림 대회 입상", "description": "재능을 발견했다.", "happiness": 5, "stats": {"센스": 5}}],
    "청년기": [{"name": "장학금", "description": "성적 장학금을 받았다.", "money": 500_000, "stats": {"지력": 5}},
              {"name": "동아리 우승", "description": "팀과 함께 우승했다.", "happiness": 10, "stats": {"체력": 5}}],
    "성년기": [{"name": "승진", "description": "능력을 인정받았다.", "money": 1_000_000, "happiness": 5}],
    "중년기": [{"name": "복권 당첨", "description": "3등에 당첨됐다.", "money": 1_500_000}],
    "노년기": [{"name": "손주 탄생", "description": "집안에 웃음이 가득하다.", "happiness": 20}],
}
BADLUCK_EVENTS = {
    "유아기": [{"name": "독감", "description": "일주일을 앓았다.", "happiness": -5, "stats": {"체력": -5}, "stat": "체력"}],
    "청년기": [{"name": "시험 낙방", "description": "다음을 기약하자.", "happiness": -10, "stat": "지력"}],
    "성년기": [{"name": "교통사고", "description": "수리비가 들었다.", "money": -800_000, "stat": "센스"}],
    "중년기": [{"name": "건강 이상", "description": "병원비가 들었다.", "money": -1_000_000, "happiness": -10, "stat": "체력"}],
    "노년기": [{"name": "사기 피해", "description": "보이스피싱에 당했다.", "money": -1_500_000, "stat": "지력"}],
}
ITEMS = [{"name": "책 한 권", "description": "꾸준히 읽었다.", "stats": {"지력": 5}},
         {"name": "운동화", "description": "매일 달렸다.", "stats": {"체력": 5}},
         {"name": "카메라", "description": "새 취미가 생겼다.", "happiness": 5, "stats": {"센스": 3}}]
SHOP_ITEMS = [{"name": "운동 기구", "price": 300_000, "stats": {"체력": 10}},
              {"name": "여행 상품", "price": 800_000, "happiness": 15},
              {"name": "자기계발 강의", "price": 500_000, "stats": {"지력": 8}}]


# ── 타일: 계획서의 클래스 이름을 그대로 썼다 (adapter가 클래스 이름으로 종류를 알아냄) ──
class Tile:
    name = ""


class Start(Tile):
    name = "출발"


class Luck(Tile):
    name = "행운"


class Badluck(Tile):
    name = "불행"


class Shop(Tile):
    name = "상점"


class Item(Tile):
    name = "아이템"


class FakePlayer:
    """계획서 3.3 Player 자료구조 + 요구사항에 나온 값들"""

    def __init__(self, player_id, name, character, is_npc):
        self.player_id = player_id
        self.player_name = name
        self.player_money = START_MONEY
        self.player_position = 0
        self.player_lap = 0
        self.player_age = 0                 # 인생 단계 번호 (0=유아기)
        self.player_job = ""
        self.player_happiness = START_HAPPINESS
        self.player_stats = dict(character["stats"])
        self.player_character = character["name"]
        self.is_npc = is_npc
        self.salary = BASE_SALARY
        self.finished = False               # 노년기를 마쳤는가
        self.adult_turns = 0                # 성년기 이후 지난 턴 수


class FakeModel:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        pattern = [Luck, Badluck, Item, Luck, Shop, Badluck, Luck]
        self.board = [Start()] + [pattern[i % len(pattern)]() for i in range(BOARD_SIZE - 1)]
        self.players: list = []

    def create_players(self, configs) -> None:
        chars = {c["id"]: c for c in CHARACTERS}
        self.players = [FakePlayer(i, c["name"], chars[c["character_id"]], c["is_npc"])
                        for i, c in enumerate(configs)]

    def roll_dice(self):
        return self.rng.randint(1, 6), self.rng.randint(1, 6)

    def move(self, p: FakePlayer, steps: int) -> dict:
        """원형 보드 이동 (3.4 알고리즘 1): 새 위치가 이전보다 작아지면 출발 칸 통과"""
        old = p.player_position
        p.player_position = (old + steps) % BOARD_SIZE
        result = {"passed_start": p.player_position < old, "stage_changed": False}
        if result["passed_start"]:
            p.player_lap += 1
            p.player_money += p.salary
            new_stage = p.player_lap // LAPS_PER_STAGE
            if new_stage >= len(STAGES):
                p.finished = True
            elif new_stage != p.player_age:
                p.player_age = new_stage
                result["stage_changed"] = True
        return result

    def tile_kind(self, p: FakePlayer) -> str:
        return type(self.board[p.player_position]).__name__.lower()

    def draw_event(self, p: FakePlayer, kind: str) -> dict:
        """연령대 맞춤 이벤트 (3.4 알고리즘 3) + 관련 능력치가 높을수록 불행 피해 감소"""
        stage = STAGES[p.player_age]
        table = LUCK_EVENTS if kind == "luck" else BADLUCK_EVENTS
        event = dict(self.rng.choice(table[stage]))
        event["kind"] = kind
        if kind == "badluck" and "stat" in event:
            cut = p.player_stats.get(event["stat"], 0) // 2          # 능력치 80 → 피해 40% 감소
            for key in ("money", "happiness"):
                if event.get(key):
                    event[key] = event[key] * (100 - cut) // 100
        return event

    def draw_item(self) -> dict:
        event = dict(self.rng.choice(ITEMS))
        event["kind"] = "item"
        return event

    def apply(self, p: FakePlayer, change: dict) -> None:
        p.player_money += change.get("money", 0)
        p.player_happiness = clamp(p.player_happiness + change.get("happiness", 0),
                                   HAPPINESS_MIN, HAPPINESS_MAX)
        for name, v in change.get("stats", {}).items():
            p.player_stats[name] = clamp(p.player_stats.get(name, 0) + v, STAT_MIN, STAT_MAX)

    def set_job(self, p: FakePlayer, job_id) -> None:
        job = next((j for j in JOBS if j["id"] == job_id), JOBS[-1])
        p.player_job = job["name"]
        p.salary = job["salary"]
        self.apply(p, {"happiness": job.get("happiness", 0)})

    def can_invest(self, p: FakePlayer) -> bool:
        return p.player_age >= 2 and p.adult_turns % INVEST_EVERY == 1

    def invest(self, p: FakePlayer, amount: int) -> dict:
        """투자 결과를 바로 정산하는 단순한 예시 (-30% ~ +50%)"""
        amount = clamp(amount, 0, max(0, p.player_money))
        rate = self.rng.randint(-30, 50)
        profit = amount * rate // 100
        p.player_money += profit
        return {"kind": "luck" if profit >= 0 else "badluck", "name": "투자 결과",
                "description": f"{amount:,}원 투자 → 수익률 {rate}%", "money": profit}

    def score(self, p: FakePlayer) -> int:
        return p.player_money // 10_000 + p.player_happiness * 10

    def ranking(self) -> list:
        rows = [{"name": p.player_name, "money": p.player_money, "happiness": p.player_happiness,
                 "score": self.score(p)} for p in self.players]
        return sorted(rows, key=lambda r: r["score"], reverse=True)

    def all_finished(self) -> bool:
        return all(p.finished for p in self.players)
