"""
model/data_loader.py  —  [팀원 담당] data/*.json 읽기 (규칙 문서: 데이터 파일 형식)

JSON의 "_설명", "_출처" 키는 사람이 읽는 설명이라 무시한다.
"""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FILES = ["settings", "scale", "characters", "board", "jobs", "events", "golden_keys", "shop",
         "companies", "exam_doctor", "business", "gigs", "art"]


def load_json(name: str) -> dict:
    """data/<name>.json을 읽는다. 파일이 없거나 깨졌으면 어떤 파일인지 알 수 있는 오류를 낸다."""
    raise NotImplementedError("TODO(팀원): 규칙 문서 '예외 처리' — 문제 파일을 못 읽으면 의사 선택을 막는다")


def load_all() -> dict:
    """{"settings": ..., "jobs": [...], ...} 한 번에 읽기"""
    raise NotImplementedError("TODO(팀원)")
