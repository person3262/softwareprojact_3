"""
view/popup_view.py  —  PopupView: 알림창과 선택창을 띄우는 창구 (FR-02-06 ~ FR-02-17)

PopupView는 "어떤 창을 띄울지" 고르는 창구 역할이고, 실제 창은 view/dialogs/ 의 클래스들이다.

  묻는 창 (ask_*) : 사용자가 고른 값을 돌려준다. 값의 검사·변환은 Input이 한다.
    ask_setup / ask_character        dialogs/setup.py   SetupDialog, CharacterDialog
    ask_job / ask_exam / ask_business / ask_switch_business / ask_gig / ask_artwork
                                     dialogs/job.py     JobDialog, ExamDialog, BusinessDialog, GigDialog, ArtworkDialog
    ask_shop / ask_invest
                                     dialogs/money.py   ShopDialog, InvestDialog
    ask_choice / ask_confirm         dialogs/event.py   ChoiceDialog, ConfirmDialog
  보여주는 창 (show_*) :
    show_event        행운·불행·황금열쇠·속보·정산 결과 카드   EventDialog
    show_exam_npc     NPC의 국가고시 ('고민 중...' 뒤 답 표시)  ExamDialog
    show_result       인생 성적표 → '한 판 더!'면 True          ResultDialog

모든 창은 모달(exec_)이라서, 창이 닫힐 때까지 다음 코드가 기다린다.
Input 테스트에서는 이 객체의 ask_* 함수를 가짜 함수로 바꿔 끼워 창 없이 검사한다.
"""
from __future__ import annotations

from PyQt5.QtWidgets import QDialog, QMessageBox, QWidget

from common.constants import STUDIO_SIZE
from view.dialogs.setup import SetupDialog, CharacterDialog
from view.dialogs.job import JobDialog, ExamDialog, BusinessDialog, GigDialog, ArtworkDialog
from view.dialogs.money import ShopDialog, InvestDialog
from view.dialogs.event import EventDialog, ChoiceDialog, ConfirmDialog
from view.dialogs.result import ResultDialog


class PopupView:
    def __init__(self, parent: QWidget = None):
        self.parent = parent

    # ── 묻는 창: 값을 돌려준다 (취소하면 None) ──────────────
    def ask_setup(self, validator):
        dlg = SetupDialog(validator, self.parent)
        return dlg.values() if dlg.exec_() == QDialog.Accepted else None

    def ask_character(self, player_name, characters, taken_ids):
        dlg = CharacterDialog(player_name, characters, taken_ids, parent=self.parent)
        dlg.exec_()
        return dlg.selected_id

    def ask_job(self, player_name, jobs, stats, exclude=(), allow_keep=False, heading=""):
        dlg = JobDialog(player_name, jobs, stats, exclude, allow_keep, heading, self.parent)
        dlg.exec_()
        return dlg.selected_id

    def ask_exam(self, player_name, question, level, level_name, time_limit):
        """국가고시: 고른 번호(1~4), 시간 초과면 None"""
        dlg = ExamDialog(player_name, question, level, level_name, time_limit, parent=self.parent)
        dlg.exec_()
        return dlg.answer

    def ask_confirm(self, title, question, detail="", yes_text="네", no_text="아니요") -> bool:
        dlg = ConfirmDialog(title, question, detail, yes_text, no_text, self.parent)
        dlg.exec_()
        return dlg.answer

    def ask_business(self, player_name, businesses, trend=None, rounds_left=0):
        dlg = BusinessDialog(player_name, businesses, trend, rounds_left, parent=self.parent)
        dlg.exec_()
        return dlg.selected_id

    def ask_switch_business(self, player_name, businesses, current, trend, rounds_left, money, cost, validator):
        dlg = BusinessDialog(player_name, businesses, trend, rounds_left, current=current,
                             money=money, cost=cost, validator=validator, parent=self.parent)
        dlg.exec_()
        return dlg.selected_id

    def ask_gig(self, player_name, cards, stats, rest_happiness=50):
        dlg = GigDialog(player_name, cards, stats, rest_happiness, self.parent)
        dlg.exec_()
        return dlg.selected_id

    def ask_artwork(self, player_name, artwork, studio, studio_size=STUDIO_SIZE):
        dlg = ArtworkDialog(player_name, artwork, studio, studio_size, self.parent)
        dlg.exec_()
        return dlg.sell_id

    def ask_shop(self, player_name, money, items):
        dlg = ShopDialog(player_name, money, items, self.parent)
        dlg.exec_()
        return dlg.selected_index

    def ask_invest(self, player_name, money, companies, validator):
        """투자: (회사 id, 금액) / 건너뛰면 None"""
        dlg = InvestDialog(player_name, money, companies, validator, self.parent)
        if dlg.exec_() == QDialog.Accepted:
            return dlg.company_id, dlg.amount()
        return None

    def ask_choice(self, title, question, options):
        dlg = ChoiceDialog(title, question, options, self.parent)
        dlg.exec_()
        return dlg.selected_index

    # ── 보여주는 창 ─────────────────────────────────────────
    def show_event(self, event, player_name: str = "", auto_close_ms: int = None) -> None:
        EventDialog(event, player_name, auto_close_ms, self.parent).exec_()

    def show_exam_npc(self, player_name, question, level, level_name, time_limit, answer, delay_ms=1000) -> None:
        ExamDialog(player_name, question, level, level_name, time_limit,
                   npc_answer=answer, npc_delay_ms=delay_ms, parent=self.parent).exec_()

    def show_result(self, ranking) -> bool:
        dlg = ResultDialog(ranking, self.parent)
        dlg.exec_()
        return dlg.play_again

    def show_message(self, text: str, title: str = "알림") -> None:
        QMessageBox.information(self.parent, title, text)

    def show_warning(self, text: str, title: str = "입력 확인") -> None:
        QMessageBox.warning(self.parent, title, text)

    def show_error(self, text: str, title: str = "오류") -> None:
        QMessageBox.critical(self.parent, title, text)
