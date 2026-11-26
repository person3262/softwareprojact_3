"""
model/game_state.py  —  [팀원 담당] 게임 한 판의 상태 = Controller가 부르는 Model 창구

Controller는 이 객체의 함수만 부르고, 규칙 계산은 rules/ 의 함수에 맡긴다.
함수 이름은 dev_stub/fake_model.py(FakeGame)와 비슷하게 맞춰 두었다 → 대역과 바꿔 끼우기 쉽다.
돌려주는 '이벤트 dict'는 그대로 window.show_event(event)에 넘긴다. (역할 분담 문서 › 함수 약속)
"""
import random

from model.data_loader import load_all


class GameState:
    def __init__(self, setup_rows: list, rng: random.Random = None, quick: bool = False):
        """setup_rows: Input.run_setup()이 돌려준 [{"name", "is_npc", "character_id"}, ...]
        quick=True면 settings의 quick_laps (발표용 빠른 모드)"""
        self.rng = rng or random.Random()
        self.data = None             # TODO(팀원): load_all()
        self.players = []            # TODO(팀원): Player 만들기 (시작 자금·행복은 settings)
        self.board = None            # TODO(팀원): Board(data["board"]["board"])
        self.turn_index = 0
        self.round = 1
        self.companies = []          # 투자할 기본 회사 3곳 (companies.json)
        self.trend = None            # 사업가 유행: 업종 id 또는 None
        self.trend_rounds_left = 0

    # ── 차례 (규칙 문서: 한 턴의 순서) ─────────────────────────
    def current_player(self):
        raise NotImplementedError("TODO(팀원)")

    def start_turn(self, player) -> None:
        """자기 턴 시작 처리 (성년기부터 센 턴 수 +1 등)"""
        raise NotImplementedError("TODO(팀원)")

    def roll_dice(self) -> tuple:
        raise NotImplementedError("TODO(팀원)")

    def move(self, player, steps: int) -> dict:
        """말을 옮기고 {"from", "steps", "passed_start", "old_stage", "new_stage"}를 돌려준다.
        출발 칸을 지나면 바퀴 수 +1, 단계 상승, 노년기를 마치면 player.finished = True"""
        raise NotImplementedError("TODO(팀원): 규칙 문서 '인생 단계'")

    def next_turn(self) -> list:
        """다음 사람으로. 라운드가 끝나 유행이 바뀌면 속보 문구 목록을 돌려준다 (없으면 [])"""
        raise NotImplementedError("TODO(팀원): 규칙 문서 '사업가: 업종과 유행'")

    def is_over(self) -> bool:
        raise NotImplementedError("TODO(팀원)")

    # ── 칸 효과 ──────────────────────────────────────────────
    def land(self, player) -> dict:
        """지금 칸의 효과 (board.tile_at(...).on_land). 상점·카드 사용처럼 물어볼 것이 있으면
        Controller가 먼저 묻고 아래 함수들을 부른다."""
        raise NotImplementedError("TODO(팀원)")

    def draw_event(self, player, kind: str) -> dict:
        """행운/불행 이벤트를 하나 뽑는다 (아직 적용 전). rules/events.py"""
        raise NotImplementedError("TODO(팀원)")

    def apply_event(self, player, event: dict, multiplier: int = 1) -> dict:
        """이벤트를 적용하고 화면용 이벤트 dict를 돌려준다 (불행이면 base_money, reduce_percent 등 포함)"""
        raise NotImplementedError("TODO(팀원)")

    def draw_golden_key(self, player) -> dict:
        raise NotImplementedError("TODO(팀원): rules/golden_key.py")

    def shop_items(self, player) -> list:
        raise NotImplementedError("TODO(팀원): rules/shop.py")

    def buy(self, player, item: dict) -> dict:
        raise NotImplementedError("TODO(팀원)")

    # ── 직업과 고유 장치 ─────────────────────────────────────
    def jobs_for(self, player) -> list:
        """직업 목록 (평범이는 조건 -10을 적용해서). Input/NPC ask_job에 그대로 넘긴다."""
        raise NotImplementedError("TODO(팀원): rules/jobs.py")

    def set_job(self, player, job_id: str) -> dict:
        raise NotImplementedError("TODO(팀원)")

    def exam_question(self, player) -> dict:
        raise NotImplementedError("TODO(팀원): rules/exam.py")

    def exam_time_limit(self, player) -> int:
        raise NotImplementedError("TODO(팀원)")

    def grade_exam(self, player, question: dict, answer) -> dict:
        """answer: 1~4 또는 None(시간 초과). 반환 이벤트 dict에 "passed": True/False"""
        raise NotImplementedError("TODO(팀원)")

    def business_result(self, player, dice_sum: int) -> dict:
        raise NotImplementedError("TODO(팀원): rules/business.py (예시 구현 있음)")

    def gig_cards(self) -> list:
        raise NotImplementedError("TODO(팀원): rules/gig.py")

    def settle_gig(self, player) -> dict:
        raise NotImplementedError("TODO(팀원)")

    def make_artwork(self, player) -> dict:
        raise NotImplementedError("TODO(팀원): rules/artwork.py")

    def place_artwork(self, player, artwork: dict, sell_id) -> dict:
        raise NotImplementedError("TODO(팀원)")

    # ── 수입·투자 ───────────────────────────────────────────
    def apply_income(self, player, steps: int, dice_sum: int) -> dict:
        """{"money", "happiness", "event"(사업가 실적 카드 또는 None)}"""
        raise NotImplementedError("TODO(팀원): rules/income.py")

    def invest_ready(self, player) -> bool:
        raise NotImplementedError("TODO(팀원): rules/invest.py")

    def invest(self, player, company_id: str, amount: int) -> dict:
        raise NotImplementedError("TODO(팀원)")

    def settle_investments(self, player) -> list:
        raise NotImplementedError("TODO(팀원)")

    # ── 끝 ──────────────────────────────────────────────────
    def finish(self) -> None:
        """정산 안 된 투자의 원금을 돌려준다"""
        raise NotImplementedError("TODO(팀원)")

    def ranking(self) -> list:
        """[{"name", "job", "money", "happiness", "score", "character", "is_npc"}, ...] 총점 순"""
        raise NotImplementedError("TODO(팀원): rules/score.py")
