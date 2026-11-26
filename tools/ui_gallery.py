"""
tools/ui_gallery.py  —  화면 모음: 모든 창을 예시 데이터로 하나씩 띄워 본다 (팀장 확인용)

    python tools/ui_gallery.py              창을 하나씩 띄운다 (닫으면 다음 창)
    python tools/ui_gallery.py --save shots 창을 띄우지 않고 shots/ 폴더에 PNG로 저장한다

발표 자료에 넣을 화면 캡처도 이걸로 만들면 된다.
"""
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PyQt5.QtWidgets import QApplication, QDialog   # noqa: E402

from dev_stub import fake_data as D                   # noqa: E402
from dev_stub.fake_model import FakeGame              # noqa: E402
from user_input.validators import validate_setup, validate_invest, validate_switch  # noqa: E402
from view import Window                               # noqa: E402
from view.style import apply_app_font                 # noqa: E402
from view.dialogs.setup import SetupDialog, CharacterDialog                                     # noqa: E402
from view.dialogs.job import JobDialog, ExamDialog, BusinessDialog, GigDialog, ArtworkDialog    # noqa: E402
from view.dialogs.money import ShopDialog, InvestDialog                                         # noqa: E402
from view.dialogs.event import EventDialog, ChoiceDialog, ConfirmDialog                         # noqa: E402
from view.dialogs.result import ResultDialog                                                    # noqa: E402

STATS = {"지력": 62, "체력": 45, "센스": 48}
STUDIO = [{"id": "a1", "title": "냉장고 속 우주", "grade": "수작", "price": 300},
          {"id": "a2", "title": "퇴근 5분 전", "grade": "습작", "price": 100}]
NEW_ART = {"id": "a3", "title": "새벽 3시 라면", "grade": "명작", "price": 800}
SHOP = [dict(i, price=500) if i.get("stat") else dict(i, price=200) for i in D.SHOP]
for item in SHOP:
    if item.get("stat"):
        item["stats"] = {item["stat"]: 3}


def sample_events():
    return {
        "event_luck": {"kind": "luck", "name": "당직 수당 두둑", "description": "주말 당직을 몰아 섰더니 통장이 든든하다.",
                       "money": 500, "stage_label": "성년기 · 의사"},
        "event_badluck": {"kind": "badluck", "name": "36시간 연속 당직", "description": "눈 뜨고 자는 법을 터득했다...",
                          "happiness": -41, "base_happiness": -50, "reduce_stat": "체력", "reduce_value": 34,
                          "reduce_percent": 18, "stage_label": "성년기 · 의사"},
        "event_golden_key": {"kind": "golden_key", "name": "불운→행운 변경권", "description": "불행 칸에서 쓰면 같은 단계 행운으로",
                             "lines": ["보관함에 넣었다. (최대 3장)"]},
        "event_business": {"kind": "business", "name": "NFT 갤러리 실적: 대박", "description": "주사위 합 9 + 3 = 12",
                           "money": 3500, "happiness": 30},
        "event_gig": {"kind": "gig", "name": "의뢰 정산: 진상 클라이언트", "money": 840,
                      "lines": ["보수 1,400만원", "정산 주사위 2 + 4 = 6", "사고: 잔금 받기 전에 잠수 (지력 40로 피해 감소)"]},
        "event_invest": {"kind": "invest", "name": "미래바이오 투자 결과", "money": 2400, "happiness": 20,
                         "lines": ["주사위 5 + 5 = 10 → ×1.6"]},
        "event_exam": {"kind": "exam", "name": "의대생이 됐다!", "description": "다음 턴부터 주사위를 굴릴 때마다 국가고시를 본다."},
    }


def build_dialogs():
    """(파일 이름, 창 만드는 함수) 목록"""
    q = D.EXAM[3]
    gigs = [g for g in D.GIGS if g["id"] in ("jerk", "friend", "startup")]
    ranking = [{"name": "정민", "job": "의사", "money": 12400, "happiness": 520, "character": "범생이"},
               {"name": "하늘", "job": "사업가", "money": 15800, "happiness": 210, "character": "운동부"},
               {"name": "민지", "job": "예술가", "money": 3900, "happiness": 1130, "character": "감성러"},
               {"name": "로봇", "job": "공무원", "money": 9800, "happiness": 650, "character": "평범이", "is_npc": True}]
    dialogs = [
        ("setup", lambda: SetupDialog(validate_setup)),
        ("character", lambda: CharacterDialog("정민", D.CHARACTERS, ["athlete"])),
        ("job", lambda: JobDialog("정민", D.JOBS, STATS)),
        ("exam", lambda: ExamDialog("정민", q, q["level"], "재수", 16)),
        ("exam_npc", lambda: ExamDialog("로봇", q, q["level"], "재수", 16, npc_answer=2, npc_delay_ms=60000)),
        ("business", lambda: BusinessDialog("하늘", D.BUSINESSES, "nft", 2)),
        ("business_switch", lambda: BusinessDialog(
            "하늘", D.BUSINESSES, "nft", 2, current="youtube", money=2400, cost=1000,
            validator=lambda new: validate_switch(2400, "youtube", new, 1000, [b["id"] for b in D.BUSINESSES]))),
        ("gig", lambda: GigDialog("민지", gigs, {"지력": 40, "체력": 45, "센스": 58})),
        ("artwork_full", lambda: ArtworkDialog("소희", NEW_ART, STUDIO)),
        ("shop", lambda: ShopDialog("정민", 700, SHOP)),
        ("invest", lambda: InvestDialog("정민", 4200, D.COMPANIES,
                                        lambda cid, amount: validate_invest(cid, amount, 4200, [c["id"] for c in D.COMPANIES]))),
        ("choice", lambda: ChoiceDialog("지갑을 주웠다", "어떻게 할까?", ["가진다: 돈 +50만원, 행복 -1", "돌려준다: 돈 +30만원, 행복 +3"])),
        ("confirm", lambda: ConfirmDialog("황금열쇠", "불운→행운 변경권을 쓸까요?", "이번 이벤트: 의료 분쟁 (돈 -많이)", "쓸래요", "아껴 둘래요")),
        ("result", lambda: ResultDialog(ranking)),
    ]
    for name, event in sample_events().items():
        dialogs.append((name, lambda e=event: EventDialog(e, "정민")))
    return dialogs


def main_window_mid_game(turns: int = 40) -> Window:
    """가짜 게임을 몇 턴 돌린 상태의 메인 창"""
    w = Window()
    rows = [{"name": n, "is_npc": npc, "character_id": c} for n, npc, c in
            [("정민", False, "scholar"), ("하늘", False, "athlete"), ("민지", False, "dreamer"), ("로봇", True, "normal")]]
    game = FakeGame(rows, random.Random(7))
    jobs = ["doctor", "business", "artist", "civil"]
    for n in range(turns):
        p = game.current_player()
        d1, d2 = game.roll_dice()
        game.move(p, d1 + d2)
        kind = game.board[p.player_position]
        if kind in ("luck", "badluck"):
            game.apply_event(p, game.draw_event(p, kind))
        game.apply_income(p, d1 + d2, d1 + d2)
        if p.player_age >= 2 and p.job_state == "none":
            game.set_job(p, jobs[p.player_id])
            if p.player_job is None:          # 의대생 → 데모용으로 바로 합격 처리
                p.job_state, p.player_job = "employed", game.find_job("doctor")
            if jobs[p.player_id] == "business":
                game.set_business(p, "nft")
        game.next_turn()
    w.set_board(game.board)
    w.set_players(game.players)
    w.set_current_player(game.current_player())
    w.set_round(game.round)
    w.show_news(game._headline(game.trend, 0))
    w.set_trend(game.trend_label())
    w.dice_view.show_result(4, 3)
    return w


def main() -> None:
    save_dir = sys.argv[sys.argv.index("--save") + 1] if "--save" in sys.argv else None
    if save_dir:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        os.makedirs(save_dir, exist_ok=True)
    app = QApplication(sys.argv)
    apply_app_font(app)

    window = main_window_mid_game()
    window.resize(1440, 900)
    if save_dir:
        window.show()
        end = time.time() + 1.0              # 주사위 애니메이션이 끝날 때까지 기다린다
        while time.time() < end:
            app.processEvents()
        window.grab().save(os.path.join(save_dir, "00_main.png"))
    for i, (name, make) in enumerate(build_dialogs(), start=1):
        dlg = make()
        if save_dir:
            dlg.show()
            dlg.adjustSize()
            app.processEvents()
            dlg.grab().save(os.path.join(save_dir, f"{i:02d}_{name}.png"))
            QDialog.done(dlg, 0)      # 작업실이 꽉 찬 창은 reject()가 경고를 띄우므로 바로 닫는다
            dlg.deleteLater()
        else:
            QDialog.exec_(dlg)
    if save_dir:
        print(f"{save_dir}/ 에 저장했습니다.")
    else:
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
