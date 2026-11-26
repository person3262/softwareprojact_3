"""입력 검사 (user_input/validators.py) — 게임 규칙 문서 '예외 처리' 표의 메시지와 같은지"""
import unittest

from tests import helpers  # noqa: F401  (경로 준비)
from user_input.validators import (validate_name, validate_setup, parse_amount, validate_amount, validate_invest,
                                   validate_switch, validate_exam_answer,
                                   MSG_NAME_EMPTY, MSG_NAME_DUP, MSG_NAME_LONG, MSG_NPC_LIMIT, MSG_NOT_NUMBER,
                                   MSG_NEGATIVE, MSG_OVER_MONEY, MSG_NO_COMPANY, MSG_SWITCH_NO_MONEY, MSG_SWITCH_SAME)


class TestSetup(unittest.TestCase):
    def test_names(self):
        self.assertEqual(validate_name("  ", []), MSG_NAME_EMPTY)
        self.assertEqual(validate_name("정민", ["정민"]), MSG_NAME_DUP)
        self.assertEqual(validate_name("가" * 11, []), MSG_NAME_LONG)
        self.assertEqual(validate_name("가" * 10, []), "")

    def test_setup_rows(self):
        ok = [{"name": "정민", "is_npc": False}, {"name": "로봇", "is_npc": True}]
        self.assertEqual(validate_setup(ok), "")
        two_npc = [{"name": "가", "is_npc": True}, {"name": "나", "is_npc": True}]
        self.assertEqual(validate_setup(two_npc), MSG_NPC_LIMIT)
        dup = [{"name": "가", "is_npc": False}, {"name": "가", "is_npc": False}]
        self.assertIn(MSG_NAME_DUP, validate_setup(dup))


class TestMoney(unittest.TestCase):
    def test_parse_amount(self):
        self.assertEqual(parse_amount("1,500"), 1500)
        self.assertEqual(parse_amount(" 1,500 만원 "), 1500)
        self.assertEqual(parse_amount("-30"), -30)
        self.assertIsNone(parse_amount("abc"))
        self.assertEqual(parse_amount(700), 700)

    def test_invest_messages(self):
        self.assertEqual(validate_amount("abc", 1000), MSG_NOT_NUMBER)
        self.assertEqual(validate_amount("-1", 1000), MSG_NEGATIVE)
        self.assertEqual(validate_amount("1001", 1000), MSG_OVER_MONEY)
        self.assertEqual(validate_amount("0", 1000), "")             # 0 = 건너뛰기
        self.assertEqual(validate_invest(None, 500, 1000, ["a"]), MSG_NO_COMPANY)
        self.assertEqual(validate_invest("a", 500, 1000, ["a"]), "")


class TestBusinessAndExam(unittest.TestCase):
    def test_switch(self):
        ids = ["store", "youtube", "nft"]
        self.assertEqual(validate_switch(500, "youtube", "nft", 1000, ids), MSG_SWITCH_NO_MONEY)
        self.assertEqual(validate_switch(5000, "nft", "nft", 1000, ids), MSG_SWITCH_SAME)
        self.assertEqual(validate_switch(5000, "youtube", "nft", 1000, ids), "")

    def test_exam_answer(self):
        self.assertEqual(validate_exam_answer(3), 3)
        self.assertIsNone(validate_exam_answer(None))     # 시간 초과
        self.assertIsNone(validate_exam_answer(7))


if __name__ == "__main__":
    unittest.main()
