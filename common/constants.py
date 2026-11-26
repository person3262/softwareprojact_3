"""
common/constants.py  —  팀장·팀원이 함께 쓰는 약속 값 (게임 규칙 문서 기준)

Model(팀원)과 View·Input·NPC(팀장)가 모두 이 값을 본다.
값을 바꿀 때는 혼자 바꾸지 말고 서로 알린 뒤, 게임 규칙 문서도 같이 고친다.
"""

# ── 보드와 인생 단계 ──────────────────────────────────────────
BOARD_SIZE = 28                                            # 8×8 격자의 테두리
STAGES = ["유아기", "청년기", "성년기", "중년기", "노년기"]    # player_age 0~4
LAPS_PER_STAGE = [1, 1, 2, 2, 1]                           # 단계별 바퀴 수 (합계 7)

# ── 능력치와 점수 ─────────────────────────────────────────────
STAT_NAMES = ["지력", "체력", "센스"]
STAT_MIN, STAT_MAX = 0, 100
HAPPINESS_WEIGHT = 10                                      # 총점 = 돈(만원) + 행복 × 10


def total_score(money: int, happiness: int) -> int:
    """총점 = 돈(만원) + 행복도 × 10. 돈은 만원 단위 정수다."""
    return int(money) + int(happiness) * HAPPINESS_WEIGHT


# ── 칸 종류 (Board 리스트의 값, Tile 클래스 이름과 짝) ─────────────
TILE_KINDS = ["start", "luck", "badluck", "golden_key", "rest", "shop"]
TILE_KIND_NAMES = {
    "start": "출발", "luck": "행운", "badluck": "불행",
    "golden_key": "황금열쇠", "rest": "휴식", "shop": "상점",
}
TILE_KIND_HINTS = {          # 칸 아래 작은 설명
    "start": "한 단계 성장!", "golden_key": "카드 뽑기", "rest": "1턴 쉬기", "shop": "능력치·보험",
}

# ── 직업 ──────────────────────────────────────────────────────
JOB_STATES = ("none", "student", "employed")   # 직업 없음 / 의대생 / 직업 있음
EXAM_LEVEL_NAMES = {1: "첫 도전", 2: "재수", 3: "삼수", 4: "사수", 5: "오수 (마지막 기회)"}
BUSINESS_TIERS = ["적자", "보통", "호황", "대박"]
STUDIO_SIZE = 2                                  # 예술가 작업실 칸 수

# ── 투자 ──────────────────────────────────────────────────────
COMPANY_TYPES = {"stable": "안정형", "growth": "성장형", "gamble": "도박형"}
INVEST_BUCKETS = ["2~3", "4~5", "6~8", "9~10", "11~12"]   # 투자 결과 주사위 합 구간
