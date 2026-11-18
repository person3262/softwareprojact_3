"""
common/adapter.py  —  팀원 Model 데이터 → 내 모듈(View·Input·NPC)용 표준 형태

왜 이 파일이 필요한가?
  View와 NPC가 player.player_money 처럼 Model의 속성 이름을 여기저기서 직접 쓰면,
  팀원이 이름을 하나만 바꿔도 내 코드 여러 곳을 고쳐야 한다.
  그래서 "Model의 값을 읽는 곳"을 이 파일 하나로 모았다.

  - 팀원 코드의 속성 이름이 다르면 → 아래 *_FIELDS 표의 후보 이름만 고치면 된다.
  - 객체(player.player_money)든 딕셔너리(player["player_money"])든 둘 다 읽을 수 있다.
  - 값이 없거나 이상해도 기본값으로 읽어서 화면이 죽지 않게 한다. (NFR-04 안정성)
"""
from __future__ import annotations

from dataclasses import dataclass, field

# ──────────────────────────────────────────────────────────────
# 게임 공통 상수 (계획서 기준)
# ──────────────────────────────────────────────────────────────
BOARD_SIZE = 28                                    # 보드 칸 수 (3.3 Board: 크기 28)
STAGES = ["유아기", "청년기", "성년기", "중년기", "노년기"]  # FR-01-11 인생 단계
STAT_NAMES = ["지력", "체력", "센스"]               # FR-01-09 능력치
STAT_MIN, STAT_MAX = 0, 100                        # 2.5 예외: 능력치 범위 보정 0~100
HAPPINESS_MIN, HAPPINESS_MAX = 0, 100

# ──────────────────────────────────────────────────────────────
# Model 속성 이름 표: "내가 쓰는 이름" → "Model에서 찾아볼 이름 후보들"
#   앞에 있는 후보부터 차례로 찾는다. 팀원 코드와 다르면 여기만 수정!
# ──────────────────────────────────────────────────────────────
PLAYER_FIELDS = {
    # 계획서 3.3 Player 자료구조에 있는 이름
    "id":        ("player_id", "id"),
    "name":      ("player_name", "name"),
    "money":     ("player_money", "money"),
    "position":  ("player_position", "position"),
    "lap":       ("player_lap", "lap"),
    "stage":     ("player_age", "stage", "age"),
    "job":       ("player_job", "job"),
    # 요구사항(FR-01-06, 09, 13)에는 있지만 자료구조 표에 아직 없는 값 → 팀원과 이름 확정 필요
    "happiness": ("player_happiness", "happiness"),
    "stats":     ("player_stats", "stats"),
    "character": ("player_character", "character"),
    "is_npc":    ("is_npc", "player_is_npc", "npc"),
}

TILE_FIELDS = {
    "kind": ("tile_type", "kind", "type"),
    "name": ("tile_name", "name"),
}
# Tile 클래스 이름으로 칸 종류를 알아낸다 (3.3 Model: Luck, Badluck, Shop, Item)
TILE_CLASS_TO_KIND = {
    "Start": "start", "StartTile": "start",
    "Luck": "luck", "Badluck": "badluck", "BadLuck": "badluck",
    "Shop": "shop", "Item": "item",
}


# ──────────────────────────────────────────────────────────────
# 내 모듈이 쓰는 표준 데이터 모양
# ──────────────────────────────────────────────────────────────
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


@dataclass
class TileInfo:
    kind: str          # "start" / "luck" / "badluck" / "shop" / "item" / "normal"
    name: str = ""


@dataclass
class EventInfo:
    kind: str          # "luck" / "badluck" / 그 밖의 문자열
    name: str
    description: str = ""
    money: int = 0     # 자금 변화량
    happiness: int = 0 # 행복도 변화량
    stats: dict = field(default_factory=dict)  # 능력치 변화량 {"지력": +5}


@dataclass
class JobInfo:
    id: str
    name: str
    salary: int = 0
    requirements: dict = field(default_factory=dict)  # {"지력": 70}
    happiness: int = 0  # 직업이 주는 행복도 보너스(있으면)


@dataclass
class ItemInfo:
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


# ──────────────────────────────────────────────────────────────
# 내부 도우미
# ──────────────────────────────────────────────────────────────
def pick(obj, names, default=None):
    """obj가 딕셔너리든 객체든, names 후보 중 먼저 발견되는 값을 돌려준다."""
    if obj is None:
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


def _name_of(value) -> str:
    """직업·캐릭터가 문자열이 아니라 객체/딕셔너리여도 이름만 꺼낸다."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(pick(value, ("name", "job_name", "character_name", "id"), ""))


def _read_stats(raw) -> dict:
    """능력치를 {"지력": 0~100, "체력": .., "센스": ..} 모양으로 맞춘다."""
    stats = {}
    for stat in STAT_NAMES:
        stats[stat] = clamp(to_int(pick(raw, (stat,), 0)), STAT_MIN, STAT_MAX)
    return stats


def _read_delta_stats(raw) -> dict:
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


# ──────────────────────────────────────────────────────────────
# 외부에서 쓰는 read_* 함수들
# ──────────────────────────────────────────────────────────────
def read_player(p) -> PlayerInfo:
    if isinstance(p, PlayerInfo):
        return p
    f = PLAYER_FIELDS
    return PlayerInfo(
        id=to_int(pick(p, f["id"], 0)),
        name=str(pick(p, f["name"], "?")),
        money=to_int(pick(p, f["money"], 0)),
        position=to_int(pick(p, f["position"], 0)) % BOARD_SIZE,
        lap=to_int(pick(p, f["lap"], 0)),
        stage=stage_name(pick(p, f["stage"], 0)),
        job=_name_of(pick(p, f["job"], "")),
        happiness=clamp(to_int(pick(p, f["happiness"], 0)), HAPPINESS_MIN, HAPPINESS_MAX),
        stats=_read_stats(pick(p, f["stats"], {})),
        character=_name_of(pick(p, f["character"], "")),
        is_npc=bool(pick(p, f["is_npc"], False)),
    )


def read_tile(t) -> TileInfo:
    if isinstance(t, TileInfo):
        return t
    kind = pick(t, TILE_FIELDS["kind"], None)
    if kind is None:  # 속성이 없으면 클래스 이름(Luck, Badluck …)으로 판단
        kind = TILE_CLASS_TO_KIND.get(type(t).__name__, "normal")
    return TileInfo(kind=str(kind).lower(), name=str(pick(t, TILE_FIELDS["name"], "")))


def read_event(e) -> EventInfo:
    if isinstance(e, EventInfo):
        return e
    return EventInfo(
        kind=str(pick(e, ("kind", "type", "event_type"), "event")).lower(),
        name=str(pick(e, ("name", "event_name", "title"), "이벤트")),
        description=str(pick(e, ("description", "desc", "text"), "")),
        money=to_int(pick(e, ("money", "money_change"), 0)),
        happiness=to_int(pick(e, ("happiness", "happiness_change"), 0)),
        stats=_read_delta_stats(pick(e, ("stats", "stat_change"), {})),
    )


def read_job(j) -> JobInfo:
    if isinstance(j, JobInfo):
        return j
    name = str(pick(j, ("name", "job_name"), "?"))
    return JobInfo(
        id=str(pick(j, ("id", "job_id"), name)),
        name=name,
        salary=to_int(pick(j, ("salary",), 0)),
        requirements={k: to_int(v) for k, v in (pick(j, ("requirements", "require"), {}) or {}).items()},
        happiness=to_int(pick(j, ("happiness",), 0)),
    )


def read_item(i) -> ItemInfo:
    if isinstance(i, ItemInfo):
        return i
    return ItemInfo(
        name=str(pick(i, ("name", "item_name"), "?")),
        price=to_int(pick(i, ("price",), 0)),
        money=to_int(pick(i, ("money",), 0)),
        happiness=to_int(pick(i, ("happiness",), 0)),
        stats=_read_delta_stats(pick(i, ("stats",), {})),
        description=str(pick(i, ("description", "desc"), "")),
    )


def read_character(c) -> CharacterInfo:
    if isinstance(c, CharacterInfo):
        return c
    name = str(pick(c, ("name", "character_name"), "?"))
    return CharacterInfo(
        id=str(pick(c, ("id", "character_id"), name)),
        name=name,
        stats=_read_stats(pick(c, ("stats",), {})),
        trait=str(pick(c, ("trait", "trait_description"), "")),
    )


def meets_requirements(stats: dict, requirements: dict) -> bool:
    """직업 조건 검사: 요구 능력치를 모두 넘으면 True. (FR-01-12, FR-02-08)"""
    return all(to_int(stats.get(k, 0)) >= to_int(v) for k, v in (requirements or {}).items())
