# 인생마불 (softwareprojact_3)

부루마불 + 인생게임. 주사위를 굴려 유아기부터 노년기까지 7바퀴를 돌고, **돈(만원) + 행복 × 10** 총점으로 순위를 가린다.
Python + PyQt5, 2인 팀 (팀장: View·Input·NPC / 팀원: Model·Controller·data).

## 실행

```bash
pip install -r requirements.txt
python run_demo.py              # 데모: 팀장 모듈 + 가짜 Model (빠른 모드, 단계마다 1바퀴)
python run_demo.py --full       # 데모: 규칙대로 7바퀴
python main.py                  # 진짜 게임 (팀원 Controller·Model 완성 후)
python tools/ui_gallery.py      # 모든 창을 예시 데이터로 하나씩 띄워 보기 (--save 폴더 → PNG 저장)
python -m unittest discover tests   # 테스트 (화면 없이 돌아감)
```

## 폴더와 담당

| 폴더 | 담당 | 상태 | 내용 |
|---|---|---|---|
| `view/` | 팀장 | 완성 | 메인 창, 보드, 상태창, 주사위, 모든 대화창 (`view/dialogs/`), 글꼴(Jua) |
| `user_input/` | 팀장 | 완성 | 버튼 클릭 감지·잠금, 입력 검사(`validators.py`), 묻는 창 열고 값 변환 |
| `npc/` | 팀장 | 완성 | NPC 판단 (Qt 없음, Input과 함수 모양이 같음) |
| `common/` | 공용 | 완성 | `constants.py` 공용 숫자, `adapter.py` Model 값 → 화면용 값 |
| `dev_stub/` | 팀장 | 완성 | 가짜 Model·Controller (데모·테스트용 대역, 최종 제출에서는 빼도 됨) |
| `tools/` | 팀장 | 완성 | `ui_gallery.py` 화면 모음 |
| `model/` | 팀원 | 뼈대 | Player, Tile, Board, Dice, Company, GameState, `rules/` 규칙 함수 (사업가는 예시 구현) |
| `controller/` | 팀원 | 뼈대 | GameController: 한 턴의 순서 8단계 |
| `data/` | 팀원 | 예시만 | 게임 수치 JSON 13개 (각 파일에 예시 1~2개, 나머지는 규칙 문서 표를 옮겨 넣기) |
| `tests/` | 둘 다 | | `test_model.py`는 팀원용 (구현하면 `@skip` 지우기), 나머지는 팀장 모듈 |

뼈대 파일의 `TODO(팀원)` 자리를 채우면 된다. 함수 안의 설명(docstring)에 규칙 문서의 어느 부분인지 적어 두었다.

## 문서

- **게임 규칙과 설정** — 전체 규칙, 수치, 이벤트 표, 예외 처리, 데이터 형식
- **역할 분담 (팀장·팀원)** — 누가 무엇을 하는지, 함수 약속, 일정, 깃 규칙
- **코드 설명서 (View·Input·NPC)** — 팀장 코드의 구조와 형식

## 약속 몇 가지

- 금액은 모두 **만원 단위 정수**. 계산은 곱한 뒤 정수 나눗셈.
- 사람/NPC 구분은 Controller의 `decider()` 한 곳에서만: `decider(p).ask_job(p, jobs)`.
- 기다림은 `QTimer`로만 (`time.sleep` 금지). 대화창은 모달이라 닫힐 때까지 기다린다.
- Model 속성 이름을 바꾸면 `common/adapter.py`의 `PLAYER_FIELDS` 표도 같이 고친다.
