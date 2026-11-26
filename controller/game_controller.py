"""
controller/game_controller.py  —  [팀원 담당] 게임 진행

규칙 문서 '한 턴의 순서' 8단계를 이 순서대로 부른다.
  1 휴식 확인 → 2 주사위 → 3 국가고시(의대생) → 4 이동(출발 칸: 단계·직업·고유 장치)
  → 5 칸 효과 → 6 매 턴 수입 → 7 투자 → 8 다음 사람

팀장 모듈을 부르는 법 (자세한 표는 '역할 분담' 문서 › 함수 약속)
  화면   : self.window.set_players(...), refresh(...), show_dice(d1, d2, on_done), move_piece(...),
           show_event(event, 이름), show_income(...), show_news(...), set_trend(...), show_result(...)
  묻기   : self.decider(p).ask_job(p, jobs) … 사람이면 Input, NPC면 NPC가 같은 모양으로 답한다
  버튼   : self.input.unlock() / unlock_actions(can_invest) / lock()
  NPC    : 기다림은 QTimer.singleShot(self.npc.think_delay_ms(), 다음_함수)  (time.sleep 금지)

★ dev_stub/fake_controller.py가 같은 흐름을 간단한 가짜 Model로 돌리는 예시다. 흐름을 볼 때 참고한다.
"""
from PyQt5.QtCore import QObject


class GameController(QObject):
    def __init__(self, window, input_handler, npc, quick: bool = False):
        super().__init__(window)
        self.window = window
        self.input = input_handler
        self.npc = npc
        self.quick = quick
        self.game = None                     # model.game_state.GameState
        # 사용자가 먼저 누르는 버튼 (Input이 감지해서 시그널로 알려 준다)
        self.input.roll_requested.connect(self.roll)
        self.input.invest_requested.connect(self.human_invest)
        self.input.end_turn_requested.connect(self.next_player)

    def decider(self, player):
        """사람이면 Input, NPC면 NPC. 함수 이름·인자·반환값이 같아서 그대로 바꿔 끼운다."""
        return self.npc if player.is_npc else self.input

    # ── 게임 시작 ───────────────────────────────────────────────
    def start(self) -> None:
        """설정 창 → GameState 만들기 → 화면 초기화 → 첫 턴
        rows = self.input.run_setup(characters, self.npc.choose_character)  (취소하면 None)"""
        raise NotImplementedError("TODO(팀원)")

    # ── 한 턴 ───────────────────────────────────────────────────
    def start_turn(self) -> None:
        """1 휴식 확인. 사람이면 self.input.unlock(), NPC면 self.input.lock() 후 QTimer로 self.roll"""
        raise NotImplementedError("TODO(팀원)")

    def roll(self) -> None:
        """2 주사위 → self.window.show_dice(d1, d2, on_done=...) 애니메이션이 끝나면 다음 단계"""
        raise NotImplementedError("TODO(팀원)")

    def exam(self, player) -> None:
        """3 국가고시 (의대생만)
        answer = self.decider(p).ask_exam_answer(p, question, time_limit, level_name)
        NPC면 self.window.show_exam_npc(...)로 고르는 모습을 보여 준다.
        떨어지면 self.decider(p).ask_retry_exam(p, level)"""
        raise NotImplementedError("TODO(팀원)")

    def after_move(self, player, result: dict) -> None:
        """4 이동 뒤: 출발 칸을 지났으면 단계 상승·직업 선택·고유 장치 → 5 → 6 → 7"""
        raise NotImplementedError("TODO(팀원)")

    def tile_effect(self, player) -> None:
        """5 칸 효과. 불행 칸에서 불운→행운 변경권이 있으면 self.decider(p).ask_use_card(p, card, event)
        상점이면 index = self.decider(p).ask_shop(p, items, jobs)"""
        raise NotImplementedError("TODO(팀원)")

    def income(self, player, steps: int, dice_sum: int) -> None:
        """6 매 턴 수입 → self.window.show_income(player_id, money, happiness)"""
        raise NotImplementedError("TODO(팀원)")

    def invest_step(self, player) -> None:
        """7 투자 정산 → 투자 기회.
        사람: self.input.unlock_actions(can_invest) 후 '턴 마치기'를 기다린다.
        NPC: self.npc.ask_invest(p, companies, players)"""
        raise NotImplementedError("TODO(팀원)")

    def human_invest(self) -> None:
        """투자하기 버튼: choice = self.input.ask_invest(p, companies, players) → {"company_id", "amount"} 또는 None"""
        raise NotImplementedError("TODO(팀원)")

    def next_player(self) -> None:
        """8 다음 사람. 유행이 바뀌면 self.window.show_news(...), set_trend(...)
        모두 끝났으면 again = self.window.show_result(ranking) → True면 self.start()"""
        raise NotImplementedError("TODO(팀원)")
