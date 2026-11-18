"""
view/style.py  —  화면에서 쓰는 색상·글꼴·숫자 표시 형식을 한곳에 모은 파일
색을 바꾸고 싶으면 이 파일만 고치면 된다.
"""
from PyQt5.QtGui import QColor, QFont, QFontDatabase

# 플레이어 순서(1~4번)별 말·카드 색
PLAYER_COLORS = ["#E74C3C", "#3498DB", "#27AE60", "#F39C12"]  # 빨강, 파랑, 초록, 주황

# 칸 종류별 배경색과 표시 이름
TILE_COLORS = {
    "start":   "#D5F5E3",
    "luck":    "#FCF3CF",
    "badluck": "#FADBD8",
    "shop":    "#D6EAF8",
    "item":    "#E8DAEF",
    "normal":  "#FFFFFF",
}
TILE_KIND_NAMES = {
    "start": "출발", "luck": "행운", "badluck": "불행",
    "shop": "상점", "item": "아이템", "normal": "",
}

BOARD_BG = "#F4F1EA"     # 보드 가운데 바탕
LINE = "#333333"         # 칸 테두리
TEXT = "#222222"
TEXT_QUIET = "#777777"
GOOD = "#1E8449"         # 증가(초록)
BAD = "#C0392B"          # 감소·빚(빨강)
HIGHLIGHT = "#111111"    # 현재 차례 강조

# 운영체제별 한글 글꼴 후보 (Windows → 맑은 고딕)
FONT_CANDIDATES = ["Malgun Gothic", "맑은 고딕", "Apple SD Gothic Neo",
                   "Noto Sans CJK KR", "NanumGothic"]


def pick_font_family() -> str:
    """설치된 한글 글꼴 중 첫 번째를 고른다."""
    installed = set(QFontDatabase().families())
    for name in FONT_CANDIDATES:
        if name in installed:
            return name
    return QFont().defaultFamily()


def apply_app_font(app, point_size: int = 10) -> None:
    app.setFont(QFont(pick_font_family(), point_size))


def player_color(order: int) -> QColor:
    """order: 0부터 시작하는 플레이어 순서"""
    return QColor(PLAYER_COLORS[order % len(PLAYER_COLORS)])


def format_money(n: int) -> str:
    """3200000 → '3,200,000원'"""
    return f"{n:,}원"


def format_delta(n: int, unit: str = "") -> str:
    """변화량 표시: +300,000원 / -10"""
    sign = "+" if n > 0 else ""
    return f"{sign}{n:,}{unit}"


def delta_color(n: int) -> str:
    return GOOD if n > 0 else BAD if n < 0 else TEXT
