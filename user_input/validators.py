"""
user_input/validators.py  —  입력 검사·변환 함수 (Qt와 무관한 순수 함수 → 단위 테스트하기 쉽다)

반환값 약속: 오류 메시지 문자열, 문제가 없으면 "" (빈 문자열)
메시지 문구는 게임 규칙 문서 '예외 처리' 표와 똑같이 맞춘다.
"""
from __future__ import annotations

NAME_MIN_LEN, NAME_MAX_LEN = 1, 10
MAX_NPC = 1     # 계획서: "플레이어 중 한 명을 NPC로 대체"

# ── 출력 메시지 (2.5 예외 처리 표 + 상세 설계 12.2) ──────────────
MSG_NAME_EMPTY = "이름을 입력하세요."
MSG_NAME_DUP = "이미 사용 중인 이름입니다."
MSG_NAME_LONG = f"이름은 {NAME_MAX_LEN}자 이하로 입력하세요."
MSG_NPC_LIMIT = f"NPC는 최대 {MAX_NPC}명까지 정할 수 있습니다."
MSG_NOT_NUMBER = "숫자를 입력하세요."
MSG_NEGATIVE = "0 이상의 금액을 입력하세요."
MSG_OVER_MONEY = "보유 금액을 초과할 수 없습니다."
MSG_NO_COMPANY = "투자할 회사를 고르세요."
MSG_SWITCH_NO_MONEY = "업종을 바꿀 비용(1,000만원)이 부족합니다."
MSG_SWITCH_SAME = "이미 그 업종입니다."
MSG_UNKNOWN_BUSINESS = "알 수 없는 업종입니다."


def validate_name(name: str, used_names) -> str:
    name = (name or "").strip()
    if len(name) < NAME_MIN_LEN:
        return MSG_NAME_EMPTY
    if len(name) > NAME_MAX_LEN:
        return MSG_NAME_LONG
    if name in used_names:
        return MSG_NAME_DUP
    return ""


def validate_setup(rows, max_npc: int = MAX_NPC) -> str:
    """rows: [{"name": "정민", "is_npc": False}, ...]"""
    used = []
    for i, row in enumerate(rows, start=1):
        message = validate_name(row.get("name", ""), used)
        if message:
            return f"플레이어 {i}: {message}"
        used.append(row["name"].strip())
    if sum(1 for r in rows if r.get("is_npc")) > max_npc:
        return MSG_NPC_LIMIT
    return ""


def parse_amount(text) -> int | None:
    """'1,500', '1500만원', ' 1,500 만원 ' 같은 입력도 받아 준다 (단위: 만원). 숫자가 아니면 None."""
    if isinstance(text, int):
        return text
    cleaned = (str(text or "")).strip().replace(",", "").replace("만원", "").replace("원", "").replace(" ", "")
    if cleaned.startswith("-") and cleaned[1:].isdigit():
        return -int(cleaned[1:])
    return int(cleaned) if cleaned.isdigit() else None


def validate_amount(amount, money: int) -> str:
    """투자 금액 검사 (만원). 0은 '건너뛰기'로 본다."""
    value = parse_amount(amount)
    if value is None:
        return MSG_NOT_NUMBER
    if value < 0:
        return MSG_NEGATIVE
    if value > max(0, money):
        return MSG_OVER_MONEY
    return ""


def validate_invest(company_id, amount, money: int, company_ids) -> str:
    """투자 화면의 '투자하기!' 검사: 회사를 골랐는지 + 금액"""
    value = parse_amount(amount)
    if value and company_id not in company_ids:
        return MSG_NO_COMPANY
    return validate_amount(amount, money)


def validate_switch(money: int, current_id, new_id, cost: int, business_ids) -> str:
    """사업가 업종 바꾸기 검사"""
    if new_id not in set(business_ids):
        return MSG_UNKNOWN_BUSINESS
    if new_id == current_id:
        return MSG_SWITCH_SAME
    if money < cost:
        return MSG_SWITCH_NO_MONEY
    return ""


def validate_exam_answer(answer):
    """시험 답: 1~4 정수만 인정, 그 밖(시간 초과 None 포함)은 None = 오답"""
    return answer if isinstance(answer, int) and 1 <= answer <= 4 else None
