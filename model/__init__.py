"""
model/  —  [팀원 담당] 게임 상태와 규칙 (Model)

  player.py      Player: 플레이어 한 명의 상태
  tile.py        Tile과 칸 종류 6가지 (Start, Luck, Badluck, GoldenKey, Rest, Shop)
  board.py       Board: 28칸 보드
  dice.py        Dice: 주사위 2개
  company.py     Company, Investment: 투자할 회사와 투자 건
  game_state.py  GameState: Controller가 부르는 Model 창구 (게임 한 판 전체 상태)
  data_loader.py data/*.json 읽기
  rules/         규칙 계산 함수 (이벤트, 수입, 직업, 국가고시, 사업가, 의뢰, 작품, 황금열쇠, 상점, 투자, 점수)

규칙은 '게임 규칙 문서'를, 내 모듈과 주고받는 값은 '역할 분담' 문서의 '함수 약속'을 본다.
dev_stub/fake_model.py에 간단화한 대역 구현이 있으니 흐름을 볼 때 참고만 한다 (그대로 복사 X).
"""
