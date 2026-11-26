"""
model/player.py  —  [팀원 담당] 플레이어 한 명의 상태

⚠ 속성 이름은 팀장의 common/adapter.py(PLAYER_FIELDS)와 약속한 이름이다.
  이름을 바꾸면 PLAYER_FIELDS 표에도 같은 이름을 넣어야 화면에 보인다.
"""
from common.constants import total_score


class Player:
    """계획서 3.3 Player 자료구조 + 상세 설계 13장에서 추가한 값"""

    def __init__(self, player_id: int, name: str, character: dict, is_npc: bool = False,
                 start_money: int = 100, start_happiness: int = 0):
        # 계획서 3.3
        self.player_id = player_id
        self.player_name = name
        self.player_money = start_money        # 만원 단위 정수. 0보다 작으면 빚 (규칙 문서: 게임 개요)
        self.player_position = 0               # 0~27 (Board 리스트 인덱스)
        self.player_lap = 0                    # 지금까지 완주한 바퀴 수 (누적, 0~7)
        self.player_age = 0                    # 인생 단계 번호 0~4 (유아기~노년기)
        self.player_job = None                 # 직업 (jobs.json의 dict). 없으면 None
        # 상세 설계 13장 추가
        self.player_happiness = start_happiness
        self.player_character = character      # characters.json의 dict
        self.player_stats = dict(character["stats"])   # {"지력": 55, "체력": 30, "센스": 35}
        self.is_npc = is_npc
        self.job_state = "none"                # "none" / "student"(의대생) / "employed"
        self.exam_level = 1                    # 국가고시 단계 1~5
        self.lecture_pass = False              # 인강 패스 (다음 시험 +10초)
        self.shop_type = None                  # 사업가 업종 (business.json의 dict)
        self.gig = None                        # 프리랜서가 맡은 의뢰 (dict) 또는 "rest"(쉬기)
        self.gig_double = False                # 다음 의뢰 보수 2배
        self.artworks = []                     # 예술가 작업실 (최대 2점)
        self.items = []                        # 보관 중인 황금열쇠 (최대 3장)
        self.investments = []                  # 정산 기다리는 투자 (Investment)
        self.skip_turns = 0                    # 쉬는 턴 수 (휴식 칸, 과로로 쓰러짐)
        self.married = False
        self.children = 0
        self.income_bonus = 0                  # 승진 횟수 0~2 (매 턴 수입 +10%씩)
        self.insurance = False                 # 보험 (다음 불행 피해 50% 감소)
        self.finished = False                  # 노년기까지 마쳤으면 True
        self.adult_turns = 0                   # 성년기부터 센 자기 턴 수 (투자 기회 계산)

    @property
    def score(self) -> int:
        """총점 = 돈 + 행복 × 10"""
        return total_score(self.player_money, self.player_happiness)

    def add_money(self, amount: int) -> int:
        """돈을 더한다 (음수면 뺀다). 0 아래로 내려가도 그대로 둔다 (빚). 실제로 더한 값을 돌려준다."""
        raise NotImplementedError("TODO(팀원): 규칙 문서 '예외 처리' — 자금이 0 미만이면 빚으로 기록")

    def add_happiness(self, amount: int) -> int:
        """행복을 더한다. 감성러는 오를 때만 ×1.1 (정수 나눗셈). 실제로 더한 값을 돌려준다."""
        raise NotImplementedError("TODO(팀원): 규칙 문서 '준비'·'이벤트 › 특성과 지속 효과'")

    def add_stat(self, name: str, amount: int) -> int:
        """능력치를 더하고 0~100으로 보정한다. 범생이는 지력이 오를 때 ×1.5. 실제로 바뀐 값을 돌려준다."""
        raise NotImplementedError("TODO(팀원): 규칙 문서 '준비', '예외 처리'(0~100 보정)")
