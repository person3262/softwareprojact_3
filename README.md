# 인생마불 — View · Input · NPC 모듈 (팀장 담당분)

Python 3 + PyQt5. 자세한 설명은 별도 "코드 설명서" 문서를 참고.

## 실행

```
pip install -r requirements.txt
python run_demo.py                       # 가짜 Model/Controller로 게임 흐름 실행
python -m unittest discover -s tests     # 단위 테스트 + 한 판 자동 진행 테스트
```

## 폴더

| 폴더 | 내용 |
| --- | --- |
| `common/adapter.py` | 팀원 Model 데이터를 읽는 유일한 곳 (속성 이름 표) |
| `view/` | Window, BoardView, PieceView, PanelView, DiceView, PopupView, style |
| `user_input/` | Input — 클릭 감지, 입력 검사·변환, 잠금 |
| `npc/` | NPC — 직업·투자·상점·선택 이벤트 결정 |
| `dev_stub/` | ⚠ 임시 가짜 Model/Controller (팀원 코드가 오면 삭제) |
| `tests/` | unittest |
