"""
common/adapter.py  —  팀원 Model 데이터 → 내 모듈(View·Input·NPC)용 표준 형태

왜 이 파일이 필요한가?
  View와 NPC가 player.player_money 처럼 Model의 속성 이름을 여기저기서 직접 쓰면,
  팀원이 이름을 하나만 바꿔도 내 코드 여러 곳을 고쳐야 한다.
  그래서 "Model의 값을 읽는 곳"을 이 파일 하나로 모았다.

  - 팀원 코드의 속성 이름이 다르면 → 아래 *_FIELDS 표의 후보 이름만 고치면 된다.
  - 객체(player.player_money)든 딕셔너리(player["player_money"])든 둘 다 읽을 수 있다.
  - 값이 없거나 이상해도 기본값으로 읽어서 화면이 죽지 않게 한다. (NFR-04 안정성)
  - 돈은 만원 단위 정수다. (게임 규칙 문서: 게임 개요)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from common.constants import (BOARD_SIZE, STAGES, STAT_NAMES, STAT_MIN, STAT_MAX,
                              TILE_KIND_NAMES, COMPANY_TYPES, total_score)

# ──────────────────────────────────────────────────────────────
# Model 속성 이름 표: "내가 쓰는 이름" → "Model에서 찾아볼 이름 후보들"
#   앞에 있는 후보부터 차례로 찾는다. 팀원 코드와 다르면 여기만 수정!
# ──────────────────────────────────────────────────────────────
PLAYER_FIELDS = {
    # 계획서 3.3 Player 자료구조
    "id":          ("player_id", "id"),
    "name":        ("player_name", "name"),
    "money":       ("player_money", "money"),
    "position":    ("player_position", "position"),
    "lap":         ("player_lap", "lap"),
    "stage":       ("player_age", "stage", "age"),
    "job":         ("player_job", "job"),
    # 상세 설계 13장에서 추가하기로 한 값
    "happiness":   ("player_happiness", "happiness"),
    "stats":       ("player_stats", "stats"),
    "character":   ("player_character", "character"),
    "is_npc":      ("is_npc", "player_is_npc", "npc"),
    "job_state":   ("job_state",),                 # "none" / "student"(의대생) / "employed"
    "exam_level":  ("exam_level",),                # 의대생 시험 단계 1~5
    "business":    ("shop_type", "business_id", "business"),   # 사업가 업종 id
    "gig":         ("gig",),                       # 프리랜서가 맡은 의뢰 (카드)
    "artworks":    ("artworks",),                  # 예술가 작업실 작품 목록
    "items":       ("items", "cards", "golden_keys"),   # 보관 중인 황금열쇠 카드
    "skip_turns":  ("skip_turns",),
    "married":     ("married",),
    "children":    ("children",),
    "income_bonus": ("income_bonus",),             # 승진 횟수 0~2
    "insurance":   ("insurance",),
    "lecture_pass": ("lecture_pass",),
    "finished":    ("finished",),
    "income_money": ("income_money",),             # 칸당 수입 (없으면 job 객체에서 찾음)
    "income_happiness": ("income_happiness",),
}

TILE_FIELDS = {
    "kind": ("tile_type", "kind", "type"),
    "name": ("tile_name", "name"),
}
# Tile 클래스 이름으로 칸 종류를 알아낸다 (상세 설계 13장: Start, Luck, Badluck, GoldenKey, Rest, Shop)
TILE_CLASS_TO_KIND = {
    "Start": "start", "StartTile": "start",
    "Luck": "luck", "LuckTile": "luck",
    "Badluck": "badluck", "BadLuck": "badluck", "BadluckTile": "badluck",
    "GoldenKey": "golden_key", "GoldenKeyTile": "golden_key", "Item": "golden_key",
    "Rest": "rest", "RestTile": "rest",
    "Shop": "shop", "ShopTile": "shop",
}


# ──────────────────────────────────────────────────────────────
# 내 모듈이 쓰는 표준 데이터 모양
# ──────────────────────────────────────────────────────────────
@dataclass
class ArtworkInfo:
    id: str
    title: str
    grade: str = ""
    price: int = 0          # 판매가(만원)


@dataclass
class PlayerInfo:
    id: int
    name: str
    money: int = 0
    position: int = 0
    lap: int = 0
    stage: str = STAGES[0]
    job: str = ""
    happiness: int = 0
    stats: dict = field(default_factory=dict)
    character: str = ""
    is_npc: bool = False
    job_state: str = "none"
    exam_level: int = 1
    business: str = ""
    gig: str = ""
    artworks: list = field(default_factory=list)
    items: list = field(default_factory=list)
    skip_turns: int = 0
    married: bool = False
    children: int = 0
    income_bonus: int = 0
    insurance: bool = False
    lecture_pass: bool = False
    finished: bool = False
    income_money: int = 0
    income_happiness: int = 0

    @property
    def score(self) -> int:
        return total_score(self.money, self.happiness)

    @property
    def stage_index(self) -> int:
        return STAGES.index(self.stage)


@dataclass
class TileInfo:
    kind: str          # "start" / "luck" / "badluck" / "golden_key" / "rest" / "shop"
    name: str = ""


@dataclass
class EventInfo:
    kind: str                  # luck, badluck, golden_key, news, business, gig, artwork, exam, invest, info
    name: str
    description: str = ""
    money: int = 0             # 실제로 바뀐 돈(만원)
    happiness: int = 0
    stats: dict = field(default_factory=dict)
    stage_label: str = ""      # "성년기 · 의사" 같은 머리말
    base_money: int = None     # 불행 피해를 줄이기 전 값 (없으면 None)
    base_happiness: int = None
    reduce_stat: str = ""      # "체력"
    reduce_value: int = 0      # 그 능력치 값 34
    reduce_percent: int = 0    # 줄어든 비율 18
    lines: list = field(default_factory=list)   # 덧붙일 설명 줄
    skip_turns: int = 0
    size: str = ""             # 조금 / 적당히 / 많이 (NPC 판단용)


@dataclass
class JobInfo:
    id: str
    name: str
    category: str = ""
    requirements: dict = field(default_factory=dict)  # {"지력": 60}
    income_money: int = 0          # 칸당 돈(만원)
    income_happiness: int = 0      # 칸당 행복
    pension: int = 50              # 연금 비율(%)
    description: str = ""
    device: str = ""               # exam / business / gig / artwork / ""
    expected_value: int = 0        # 매 턴 기대 점수 (NPC 판단용, 없으면 계산)


@dataclass
class ItemInfo:
    id: str
    name: str
    price: int = 0
    money: int = 0
    happiness: int = 0
    stats: dict = field(default_factory=dict)
    description: str = ""


@dataclass
class CharacterInfo:
    id: str
    name: str
    stats: dict = field(default_factory=dict)
    trait: str = ""
    good_jobs: str = ""


@dataclass
class CompanyInfo:
    id: str
    name: str
    type: str = "growth"            # stable / growth / gamble
    ratios_x10: list = field(default_factory=list)   # 합 2~3, 4~5, 6~8, 9~10, 11~12 배율 × 10

    @property
    def type_name(self) -> str:
        return COMPANY_TYPES.get(self.type, self.type)

    @property
    def expected_x100(self) -> int:
        """주사위 2개 확률로 낸 기대 배율 × 100 (정수). 예) 121 = ×1.21"""
        weights = [3, 7, 16, 7, 3]        # 합 2~3, 4~5, 6~8, 9~10, 11~12가 나올 경우의 수 (총 36)
        if len(self.ratios_x10) != 5:
            return 100
        return (sum(w * r for w, r in zip(weights, self.ratios_x10)) * 10 + 18) // 36   # 반올림


@dataclass
class BusinessInfo:
    id: str
    name: str
    kind: str = ""
    desc: str = ""
    table: list = field(default_factory=list)   # [[돈, 행복] × 4]: 적자·보통·호황·대박
    trend_bonus: int = 1
    off_trend: int = 0


@dataclass
class GigInfo:
    id: str
    name: str
    quote: str = ""
    pay: int = 0
    happiness: int = 0
    stats: dict = field(default_factory=dict)
    stars: int = 0                 # 0이면 대박형
    risk: tuple = ()               # 사고가 나는 정산 주사위 합 (2, 5)
    stat: str = ""                 # 사고 피해를 줄이는 능력치
    accident: dict = field(default_factory=dict)   # {"text":..., "money":..., "happiness":...}
    jackpot: tuple = ()            # 대박이 나는 정산 주사위 합 (11, 12)
    bonus: dict = field(default_factory=dict)      # {"text":..., "money":..., "double_next": True}


@dataclass
class QuestionInfo:
    id: str
    level: int
    question: str
    choices: list = field(default_factory=list)   # 보기 4개
    answer: int = 0                               # 1~4


@dataclass
class CardInfo:
    id: str
    name: str
    description: str = ""
    keep: bool = False


# ──────────────────────────────────────────────────────────────
# 내부 도우미
# ──────────────────────────────────────────────────────────────
def pick(obj, names, default=None):
    """obj가 딕셔너리든 객체든, names 후보 중 먼저 발견되는 값을 돌려준다.
    문자열·숫자는 속성을 찾지 않는다 ("abc".title 같은 str 함수가 잡히는 것을 막는다)."""
    if obj is None or isinstance(obj, (str, bytes, int, float, bool)):
        return default
    for n in names:
        if isinstance(obj, dict):
            if n in obj:
                return obj[n]
        elif hasattr(obj, n):
            return getattr(obj, n)
    return default


def to_int(value, default=0) -> int:
    """정수로 바꾼다. 실패하면 default. (NFR-03: 모든 수치는 정수)"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def name_of(value) -> str:
    """직업·캐릭터·회사가 문자열이 아니라 객체/딕셔너리여도 이름만 꺼낸다."""
    if value is None or value is False:
        return ""
    if isinstance(value, str):
        return value
    return str(pick(value, ("name", "job_name", "character_name", "title", "id"), ""))


def read_stats(raw) -> dict:
    """능력치를 {"지력": 0~100, "체력": .., "센스": ..} 모양으로 맞춘다."""
    return {stat: clamp(to_int(pick(raw, (stat,), 0)), STAT_MIN, STAT_MAX) for stat in STAT_NAMES}


def read_delta_stats(raw) -> dict:
    """능력치 '변화량'(+/-)을 읽는다. 0인 항목은 뺀다."""
    if not raw:
        return {}
    result = {}
    for stat in STAT_NAMES:
        v = to_int(pick(raw, (stat,), 0))
        if v:
            result[stat] = v
    return result


def stage_name(stage) -> str:
    """인생 단계가 숫자(0~4)로 오든 문자열로 오든 '청년기' 같은 이름으로 바꾼다."""
    if isinstance(stage, int):
        return STAGES[clamp(stage, 0, len(STAGES) - 1)]
    stage = str(stage) if stage is not None else ""
    return stage if stage in STAGES else STAGES[0]


def stage_index(stage) -> int:
    return STAGES.index(stage_name(stage))


def _int_or_none(value):
    return None if value is None else to_int(value)


def _pair(value) -> tuple:
    """[2, 5] 같은 범위를 (2, 5)로. 없으면 ()"""
    if not value:
        return ()
    try:
        low, high = value
        return to_int(low), to_int(high)
    except (TypeError, ValueError):
        return ()


# ──────────────────────────────────────────────────────────────
# 외부에서 쓰는 read_* 함수들
# ──────────────────────────────────────────────────────────────
def read_player(p) -> PlayerInfo:
    if isinstance(p, PlayerInfo):
        return p
    f = PLAYER_FIELDS
    job = pick(p, f["job"], "")
    income_money = pick(p, f["income_money"], None)
    income_happiness = pick(p, f["income_happiness"], None)
    if income_money is None and job and not isinstance(job, str):     # job이 객체면 거기서 수입을 읽는다
        income = pick(job, ("income",), {}) or {}
        income_money = pick(income, ("money",), pick(job, ("income_money",), 0))
        income_happiness = pick(income, ("happiness",), pick(job, ("income_happiness",), 0))
    gig = pick(p, f["gig"], None)
    return PlayerInfo(
        id=to_int(pick(p, f["id"], 0)),
        name=str(pick(p, f["name"], "?")),
        money=to_int(pick(p, f["money"], 0)),
        position=to_int(pick(p, f["position"], 0)) % BOARD_SIZE,
        lap=to_int(pick(p, f["lap"], 0)),
        stage=stage_name(pick(p, f["stage"], 0)),
        job=name_of(job),
        happiness=to_int(pick(p, f["happiness"], 0)),
        stats=read_stats(pick(p, f["stats"], {})),
        character=name_of(pick(p, f["character"], "")),
        is_npc=bool(pick(p, f["is_npc"], False)),
        job_state=str(pick(p, f["job_state"], "employed" if job else "none") or "none"),
        exam_level=clamp(to_int(pick(p, f["exam_level"], 1), 1), 1, 5),
        business=name_of(pick(p, f["business"], "")),
        gig=name_of(gig) if gig not in (None, "rest") else ("쉬는 중" if gig == "rest" else ""),
        artworks=[read_artwork(a) for a in (pick(p, f["artworks"], []) or [])],
        items=[name_of(i) for i in (pick(p, f["items"], []) or [])],
        skip_turns=to_int(pick(p, f["skip_turns"], 0)),
        married=bool(pick(p, f["married"], False)),
        children=to_int(pick(p, f["children"], 0)),
        income_bonus=to_int(pick(p, f["income_bonus"], 0)),
        insurance=bool(pick(p, f["insurance"], False)),
        lecture_pass=bool(pick(p, f["lecture_pass"], False)),
        finished=bool(pick(p, f["finished"], False)),
        income_money=to_int(income_money, 0),
        income_happiness=to_int(income_happiness, 0),
    )


def read_tile(t) -> TileInfo:
    if isinstance(t, TileInfo):
        return t
    if isinstance(t, str):                       # board.json처럼 "luck" 문자열만 와도 된다
        kind = t
        return TileInfo(kind=kind, name=TILE_KIND_NAMES.get(kind, ""))
    kind = pick(t, TILE_FIELDS["kind"], None)
    if kind is None:                             # 속성이 없으면 클래스 이름(Luck, Badluck …)으로 판단
        kind = TILE_CLASS_TO_KIND.get(type(t).__name__, "luck")
    kind = str(kind).lower()
    return TileInfo(kind=kind, name=str(pick(t, TILE_FIELDS["name"], TILE_KIND_NAMES.get(kind, ""))))


def read_event(e) -> EventInfo:
    if isinstance(e, EventInfo):
        return e
    lines = pick(e, ("lines",), []) or []
    return EventInfo(
        kind=str(pick(e, ("kind", "type", "event_type"), "info")).lower(),
        name=str(pick(e, ("name", "event_name", "title"), "이벤트")),
        description=str(pick(e, ("description", "desc", "text"), "") or ""),
        money=to_int(pick(e, ("money", "money_change"), 0)),
        happiness=to_int(pick(e, ("happiness", "happiness_change"), 0)),
        stats=read_delta_stats(pick(e, ("stats", "stat_change"), {})),
        stage_label=str(pick(e, ("stage_label", "label"), "") or ""),
        base_money=_int_or_none(pick(e, ("base_money",), None)),
        base_happiness=_int_or_none(pick(e, ("base_happiness",), None)),
        reduce_stat=str(pick(e, ("reduce_stat",), "") or ""),
        reduce_value=to_int(pick(e, ("reduce_value",), 0)),
        reduce_percent=to_int(pick(e, ("reduce_percent",), 0)),
        lines=[str(x) for x in lines],
        skip_turns=to_int(pick(e, ("skip_turns", "skip"), 0)),
        size=str(pick(e, ("size",), "") or ""),
    )


def read_job(j) -> JobInfo:
    if isinstance(j, JobInfo):
        return j
    name = str(pick(j, ("name", "job_name"), "?"))
    income = pick(j, ("income",), {}) or {}
    return JobInfo(
        id=str(pick(j, ("id", "job_id"), name)),
        name=name,
        category=str(pick(j, ("category",), "") or ""),
        requirements={k: to_int(v) for k, v in (pick(j, ("requirements", "require"), {}) or {}).items()},
        income_money=to_int(pick(income, ("money",), pick(j, ("income_money",), 0))),
        income_happiness=to_int(pick(income, ("happiness",), pick(j, ("income_happiness",), 0))),
        pension=to_int(pick(j, ("pension",), 50), 50),
        description=str(pick(j, ("description", "desc"), "") or ""),
        device=str(pick(j, ("device",), "") or ""),
        expected_value=to_int(pick(j, ("expected_value",), 0)),
    )


def read_item(i) -> ItemInfo:
    if isinstance(i, ItemInfo):
        return i
    name = str(pick(i, ("name", "item_name"), "?"))
    return ItemInfo(
        id=str(pick(i, ("id",), name)),
        name=name,
        price=to_int(pick(i, ("price",), 0)),
        money=to_int(pick(i, ("money",), 0)),
        happiness=to_int(pick(i, ("happiness",), 0)),
        stats=read_delta_stats(pick(i, ("stats",), {})),
        description=str(pick(i, ("description", "desc"), "") or ""),
    )


def read_character(c) -> CharacterInfo:
    if isinstance(c, CharacterInfo):
        return c
    name = str(pick(c, ("name", "character_name"), "?"))
    return CharacterInfo(
        id=str(pick(c, ("id", "character_id"), name)),
        name=name,
        stats=read_stats(pick(c, ("stats",), {})),
        trait=str(pick(c, ("trait", "trait_description"), "") or ""),
        good_jobs=str(pick(c, ("good_jobs",), "") or ""),
    )


def read_company(c) -> CompanyInfo:
    if isinstance(c, CompanyInfo):
        return c
    name = str(pick(c, ("name", "company_name"), "?"))
    return CompanyInfo(
        id=str(pick(c, ("id",), name)),
        name=name,
        type=str(pick(c, ("type", "company_type"), "growth")),
        ratios_x10=[to_int(r) for r in (pick(c, ("ratios_x10",), []) or [])],
    )


def read_business(b) -> BusinessInfo:
    if isinstance(b, BusinessInfo):
        return b
    name = str(pick(b, ("name",), "?"))
    table = [[to_int(m), to_int(h)] for m, h in (pick(b, ("table",), []) or [])]
    return BusinessInfo(
        id=str(pick(b, ("id",), name)), name=name,
        kind=str(pick(b, ("kind",), "") or ""), desc=str(pick(b, ("desc",), "") or ""),
        table=table, trend_bonus=to_int(pick(b, ("trend_bonus",), 1)),
        off_trend=to_int(pick(b, ("off_trend",), 0)),
    )


def read_gig(g) -> GigInfo:
    if isinstance(g, GigInfo):
        return g
    name = str(pick(g, ("name",), "?"))
    return GigInfo(
        id=str(pick(g, ("id",), name)), name=name,
        quote=str(pick(g, ("quote",), "") or ""),
        pay=to_int(pick(g, ("pay",), 0)),
        happiness=to_int(pick(g, ("happiness",), 0)),
        stats=read_delta_stats(pick(g, ("stats",), {})),
        stars=to_int(pick(g, ("stars",), 0)),
        risk=_pair(pick(g, ("risk",), ())),
        stat=str(pick(g, ("stat",), "") or ""),
        accident=dict(pick(g, ("accident",), {}) or {}),
        jackpot=_pair(pick(g, ("jackpot",), ())),
        bonus=dict(pick(g, ("bonus",), {}) or {}),
    )


def read_artwork(a) -> ArtworkInfo:
    if isinstance(a, ArtworkInfo):
        return a
    title = str(pick(a, ("title", "name"), "무제"))
    return ArtworkInfo(id=str(pick(a, ("id",), title)), title=title,
                       grade=str(pick(a, ("grade",), "") or ""), price=to_int(pick(a, ("price",), 0)))


def read_question(q) -> QuestionInfo:
    if isinstance(q, QuestionInfo):
        return q
    return QuestionInfo(
        id=str(pick(q, ("id",), "")), level=clamp(to_int(pick(q, ("level",), 1), 1), 1, 5),
        question=str(pick(q, ("question",), "")),
        choices=[str(c) for c in (pick(q, ("choices",), []) or [])][:4],
        answer=to_int(pick(q, ("answer",), 0)),
    )


def read_card(c) -> CardInfo:
    if isinstance(c, CardInfo):
        return c
    if isinstance(c, str):
        return CardInfo(id=c, name=c)
    name = str(pick(c, ("name",), "?"))
    return CardInfo(id=str(pick(c, ("id",), name)), name=name,
                    description=str(pick(c, ("description", "desc"), "") or ""),
                    keep=bool(pick(c, ("keep",), False)))


def meets_requirements(stats: dict, requirements: dict) -> bool:
    """직업 조건 검사: 요구 능력치를 모두 넘으면 True. (FR-01-12, FR-02-08)
    평범이의 '조건 10 낮게'는 Controller(Model)가 requirements를 줄여서 넘겨준다."""
    return all(to_int(stats.get(k, 0)) >= to_int(v) for k, v in (requirements or {}).items())
