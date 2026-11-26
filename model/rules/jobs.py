"""
model/rules/jobs.py  —  [팀원 담당] 직업 목록·조건·직업 정하기 (규칙 문서: 직업 5개와 직업 선택 규칙)
"""


def jobs_for(player, jobs: list) -> list:
    """화면·NPC에 넘길 직업 목록. 평범이는 모든 조건을 10씩 낮춘 사본을 만든다."""
    raise NotImplementedError("TODO(팀원)")


def can_choose(player, job: dict) -> bool:
    """조건을 모두 넘는지 (common.adapter.meets_requirements를 써도 된다)"""
    raise NotImplementedError("TODO(팀원)")


def become(player, job: dict) -> dict:
    """직업을 정한다. 의사는 '의대생'(job_state="student", exam_level=1)이 된다.
    직업을 바꿀 때: 맡은 의뢰는 정산, 작업실 작품은 판매가에 판다."""
    raise NotImplementedError("TODO(팀원)")
