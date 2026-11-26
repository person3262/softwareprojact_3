"""
view/style.py  —  화면의 색·글꼴·숫자 표시 형식을 한곳에 모은 파일

디자인 생각: "인생은 하루"
  - 보드 뒤 하늘이 지금 차례인 사람의 인생 단계를 따라간다.
    유아기 새벽(분홍) → 청년기 아침(하늘색) → 성년기 한낮(파랑) → 중년기 노을(주황) → 노년기 밤(남보라)
  - 손에 닿는 것(칸·말·주사위·카드·버튼)은 스티커처럼: 굵은 잉크 테두리 + 번지지 않는 그림자
  - 색은 뜻을 가진다: 행운 초록, 불행 보라, 황금열쇠 금색, 상점 파랑, 휴식 민트, 출발 체리
색을 바꾸고 싶으면 이 파일만 고치면 된다.
  - 제목·숫자·버튼: 주아체(Jua, SIL OFL) — view/fonts/Jua-Regular.ttf 를 프로그램이 직접 불러온다.
  - 본문: 맑은 고딕 (없으면 다른 한글 글꼴)
"""
from __future__ import annotations

import os

from PyQt5.QtGui import QColor, QFont, QFontDatabase

# ── 기본 색 ────────────────────────────────────────────────
INK = "#23264A"           # 테두리·글씨 (잉크 남색)
PAPER = "#FFFFFF"         # 스티커 바탕
TEXT = INK
TEXT_QUIET = "#676D90"
LINE = INK
CARD_BG = PAPER
CARD_LINE = "#C4CAE4"     # 고르지 않은 카드의 옅은 테두리
BG = "#DDF3FF"            # 창 바탕 (하늘이 그려지기 전)
BOARD_BG = "#F7F4EC"      # 보드 판 안쪽 (종이)
BOARD_DOT = "#E6E0D0"     # 보드 판 무늬

SUN = "#FFD43B"           # 주 버튼 (햇빛 노랑)
LEAF = "#2EC774"          # 행운·좋음
STORM = "#8A6CFF"         # 불행
GOLD = "#FFB21E"          # 황금열쇠·돈
POOL = "#3FA9F5"          # 상점·정보
MINT = "#22C3B0"          # 휴식
CHERRY = "#FF5D73"        # 출발·강조

GOOD = "#17A35B"          # 늘어난 값 (글씨용, 조금 진하게)
BAD = "#EC3D55"           # 줄어든 값·빚
HAPPY = "#FF4F93"         # 행복
COIN = GOLD
PRIMARY = SUN
PRIMARY_DARK = INK
SECONDARY = PAPER
ACCENT = SUN              # 7칸! 배지, 1위

# 플레이어 순서(1~4번)별 색: 체리, 하늘, 잎, 포도
PLAYER_COLORS = ["#FF5D73", "#3FA9F5", "#2DBE6C", "#A66BFF"]

# 칸 종류별 (바탕색, 강조색, 글씨색). 자주 나오는 행운·불행은 옅게, 특별한 칸은 진하게
TILE_STYLE = {
    "start":      (CHERRY, "#C7334A", "#FFFFFF"),
    "luck":       ("#E2F8EB", LEAF, "#128A4A"),
    "badluck":    ("#ECE7FF", STORM, "#5E44D6"),
    "golden_key": (GOLD, "#C98500", INK),
    "rest":       (MINT, "#13897C", "#FFFFFF"),
    "shop":       (POOL, "#1D73B8", "#FFFFFF"),
}

# 인생 단계별 하늘 (위, 아래) — 유아기 새벽 → 노년기 밤
STAGE_SKIES = [
    ("#FFB4CF", "#FFE7C7"),
    ("#6FD0FF", "#D9F5FF"),
    ("#2E9BFF", "#BDE9FF"),
    ("#FF7E57", "#FFD18A"),
    ("#1E2463", "#5847B2"),
]
# 인생 단계 대표색 (인생 지도 정류장)
STAGE_COLORS = ["#FF8FB4", "#3CC4F5", "#2E86FF", "#FF7A45", "#6A55D8"]
STAGE_HILLS = ["#9FDB8C", "#6ED17D", "#3DBA6A", "#C9A35B", "#2C3A72"]

# 투자 회사 유형 색
COMPANY_TYPE_COLORS = {"stable": LEAF, "growth": POOL, "gamble": CHERRY}

# 결과 카드 (머리 문구, 머리 바탕색, 강조색, 확인 버튼 문구)
EVENT_STYLE = {
    "luck":       ("행운 카드", "#E2F8EB", LEAF, "좋아요!"),
    "badluck":    ("불행 카드", "#ECE7FF", STORM, "괜찮아, 다음 턴!"),
    "golden_key": ("황금열쇠", "#FFF1C2", GOLD, "확인"),
    "news":       ("속보", "#FFE3E7", CHERRY, "확인"),
    "business":   ("사업 실적", "#DFF0FF", POOL, "확인"),
    "gig":        ("의뢰 정산", "#ECE7FF", STORM, "확인"),
    "artwork":    ("작품", "#FFE3F0", HAPPY, "확인"),
    "exam":       ("국가고시", "#DCF7F3", MINT, "확인"),
    "invest":     ("투자 결과", "#FFF1C2", GOLD, "확인"),
    "rest":       ("휴식", "#DCF7F3", MINT, "확인"),
    "info":       ("알림", "#EEF0F8", "#8C92B4", "확인"),
}

# ── 글꼴 ───────────────────────────────────────────────────
FONT_CANDIDATES = ["Malgun Gothic", "맑은 고딕", "Apple SD Gothic Neo",
                   "Noto Sans CJK KR", "Noto Sans KR", "NanumGothic"]
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
_TITLE_FAMILY = None      # 주아체를 불러오면 그 이름이 들어간다


def pick_font_family() -> str:
    """설치된 한글 글꼴 중 첫 번째를 고른다."""
    installed = set(QFontDatabase().families())
    for name in FONT_CANDIDATES:
        if name in installed:
            return name
    return QFont().defaultFamily()


def load_title_font() -> str:
    """view/fonts의 주아체를 불러온다. 실패하면 본문 글꼴을 쓴다."""
    global _TITLE_FAMILY
    if _TITLE_FAMILY is None:
        _TITLE_FAMILY = ""
        path = os.path.join(FONT_DIR, "Jua-Regular.ttf")
        if os.path.exists(path):
            font_id = QFontDatabase.addApplicationFont(path)
            families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
            _TITLE_FAMILY = families[0] if families else ""
    return _TITLE_FAMILY or pick_font_family()


def apply_app_font(app, point_size: int = 10) -> None:
    """QApplication을 만든 직후 한 번 부른다: 본문 글꼴 지정 + 주아체 불러오기 + 기본 스타일"""
    app.setFont(QFont(pick_font_family(), point_size))
    family = load_title_font()
    app.setStyleSheet(APP_QSS.replace("__TITLE__", family))


def title_family() -> str:
    return _TITLE_FAMILY or pick_font_family()


def title_font(pixel_size: int) -> QFont:
    """제목·숫자용 글꼴 (주아체)"""
    font = QFont(title_family())
    font.setPixelSize(pixel_size)
    return font


def body_font(pixel_size: int, bold: bool = False) -> QFont:
    font = QFont(pick_font_family())
    font.setPixelSize(pixel_size)
    font.setBold(bold)
    return font


def player_color(order: int) -> QColor:
    """order: 0부터 시작하는 플레이어 순서"""
    return QColor(PLAYER_COLORS[order % len(PLAYER_COLORS)])


def player_color_hex(order: int) -> str:
    return PLAYER_COLORS[order % len(PLAYER_COLORS)]


def darker(color: str, factor: int = 130) -> str:
    return QColor(color).darker(factor).name()


def mix(a: str, b: str, t: float) -> QColor:
    """두 색 사이 t(0~1) 지점의 색 — 하늘이 바뀔 때 쓴다"""
    ca, cb = QColor(a), QColor(b)
    return QColor(int(ca.red() + (cb.red() - ca.red()) * t), int(ca.green() + (cb.green() - ca.green()) * t),
                  int(ca.blue() + (cb.blue() - ca.blue()) * t))


# ── 숫자 표시 (돈은 만원 단위 정수) ───────────────────────────
def format_money(n: int) -> str:
    """4180 → '4,180만원', 12640 → '1억 2,640만원', 0 → '0원', -300 → '-300만원'"""
    n = int(n)
    if n == 0:
        return "0원"
    sign = "-" if n < 0 else ""
    eok, man = divmod(abs(n), 10_000)
    if eok and man:
        return f"{sign}{eok}억 {man:,}만원"
    if eok:
        return f"{sign}{eok}억원"
    return f"{sign}{man:,}만원"


def format_money_delta(n: int) -> str:
    """변화량: +700만원 / -300만원"""
    return ("+" if n > 0 else "") + format_money(n) if n else "0원"


def format_delta(n: int, unit: str = "") -> str:
    """변화량 표시: +10 / -5"""
    sign = "+" if n > 0 else ""
    return f"{sign}{n:,}{unit}"


def format_ratio_x10(r: int) -> str:
    """배율 × 10 정수 → '×1.5'"""
    return f"×{r // 10}.{r % 10}" if r % 10 else f"×{r // 10}.0"


def format_ratio_x100(r: int) -> str:
    """배율 × 100 정수 → '×1.21'"""
    return f"×{r // 100}.{r % 100:02d}"


def delta_color(n: int) -> str:
    return GOOD if n > 0 else BAD if n < 0 else TEXT


# ── 공통 스타일시트 ─────────────────────────────────────────
# 버튼은 스티커처럼: 굵은 잉크 테두리 + 아래쪽이 두꺼운 테두리(입체), 누르면 아래로 눌린다.
APP_QSS = f"""
QDialog, QMainWindow {{ background: {BG}; }}
QToolTip {{ background: {INK}; color: white; border: none; padding: 4px 8px; }}
QPushButton {{
    font-family: "__TITLE__"; background: {PAPER}; color: {INK};
    border: 3px solid {INK}; border-bottom-width: 6px; border-radius: 14px;
    padding: 4px 16px; margin-top: 0px;
}}
QPushButton:hover {{ background: #EEF4FF; }}
QPushButton:pressed {{ border-bottom-width: 3px; margin-top: 3px; }}
QPushButton:disabled {{ color: #A4AAC8; background: #EEF0F7; border-color: #B9BEDA; }}
QPushButton[role="primary"] {{ background: {SUN}; }}
QPushButton[role="primary"]:hover {{ background: #FFE066; }}
QPushButton[role="primary"]:disabled {{ background: #F3EDD2; color: #B9B193; border-color: #CBC6AE; }}
QPushButton[role="good"] {{ background: #43D688; }}
QPushButton[role="good"]:hover {{ background: #63E09D; }}
QPushButton[role="good"]:disabled {{ background: #D2F0DF; color: #8DB59E; border-color: #A9CAB7; }}
QLineEdit, QSpinBox {{
    background: white; border: 3px solid {INK}; border-radius: 12px; padding: 6px 10px; color: {INK};
    selection-background-color: {SUN}; selection-color: {INK};
}}
QLineEdit:focus, QSpinBox:focus {{ border-color: {POOL}; }}
QPlainTextEdit {{ background: white; border: 2px solid {CARD_LINE}; border-radius: 12px; color: {INK}; padding: 4px; }}
QSlider::groove:horizontal {{ height: 12px; background: #E6EAF6; border: 2px solid {INK}; border-radius: 8px; }}
QSlider::sub-page:horizontal {{ background: {POOL}; border: 2px solid {INK}; border-radius: 8px; }}
QSlider::handle:horizontal {{ background: {SUN}; border: 3px solid {INK}; width: 20px; margin: -8px 0; border-radius: 13px; }}
QProgressBar {{ background: #E6EAF6; border: none; border-radius: 4px; }}
QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{ width: 10px; background: transparent; margin: 4px 0; }}
QScrollBar::handle:vertical {{ background: rgba(35, 38, 74, 90); border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border: 3px solid {INK}; border-radius: 6px; background: white; }}
QCheckBox::indicator:checked {{ background: {SUN}; }}
QRadioButton, QCheckBox, QLabel {{ color: {INK}; }}
"""
