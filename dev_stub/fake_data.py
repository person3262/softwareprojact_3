"""
dev_stub/fake_data.py  —  데모·테스트용 가짜 데이터 (팀장 작업용, 최종 게임에서는 쓰지 않음)

모양은 게임 규칙 문서 '데이터 파일 형식'과 같다 → 팀원이 data/*.json을 채울 때 참고할 수 있다.
진짜 게임은 팀원 Model이 data/*.json을 읽는다. 금액은 모두 만원 단위 정수.
이벤트는 규칙 문서 '이벤트 표' 탭에서 일부만 옮겼다.
"""

SETTINGS = {
    "start_money": 100, "start_happiness": 0,
    "laps_per_stage": [1, 1, 2, 2, 1],
    "quick_laps": [1, 1, 1, 1, 1],          # 발표용 빠른 모드
    "invest_every": 5, "invest_wait": 5,     # 자기 턴 5번마다 기회, 5턴 뒤 정산
    "trend_rounds": 4,
    "switch_cost": 1000, "rest_happiness": 50,
}

SCALE = {   # 단계별 [조금, 적당히, 많이]
    "유아기": {"money": [10, 30, 50], "happiness": [1, 3, 5], "stat": [3, 5, 8]},
    "청년기": {"money": [20, 50, 100], "happiness": [2, 5, 10], "stat": [3, 5, 8]},
    "성년기": {"money": [200, 500, 1000], "happiness": [20, 50, 100], "stat": [2, 3, 5]},
    "중년기": {"money": [300, 700, 1500], "happiness": [30, 70, 150], "stat": [1, 2, 3]},
    "노년기": {"money": [200, 500, 1000], "happiness": [20, 50, 100], "stat": [1, 2, 3]},
}

CHARACTERS = [
    {"id": "scholar", "name": "범생이", "stats": {"지력": 55, "체력": 30, "센스": 35},
     "trait": "공부 체질: 지력이 오를 때 ×1.5", "good_jobs": "의사, 공무원"},
    {"id": "athlete", "name": "운동부", "stats": {"지력": 25, "체력": 55, "센스": 40},
     "trait": "강철 체력: 불행 피해 20% 더 감소", "good_jobs": "사업가"},
    {"id": "dreamer", "name": "감성러", "stats": {"지력": 35, "체력": 30, "센스": 55},
     "trait": "소확행: 행복이 오를 때 ×1.1", "good_jobs": "예술가, 프리랜서"},
    {"id": "normal", "name": "평범이", "stats": {"지력": 40, "체력": 40, "센스": 40},
     "trait": "적응력: 직업 조건 10씩 낮게", "good_jobs": "골고루"},
]

# 0번(출발)부터 시계방향 28칸
BOARD = ["start", "luck", "badluck", "luck", "golden_key", "badluck", "luck", "rest",
         "badluck", "luck", "badluck", "shop", "luck", "badluck", "golden_key", "luck",
         "badluck", "luck", "badluck", "luck", "badluck", "shop", "luck", "badluck",
         "luck", "badluck", "luck", "badluck"]

JOBS = [
    {"id": "doctor", "name": "의사", "category": "돈 우선", "requirements": {"지력": 60},
     "income": {"money": 100, "happiness": 1}, "pension": 50, "device": "exam",
     "description": "고르면 의대생이 되어 국가고시를 본다", "expected_value": 770},
    {"id": "business", "name": "사업가", "category": "돈 우선", "requirements": {"체력": 50, "센스": 40},
     "income": {"money": 0, "happiness": 0}, "pension": 50, "device": "business",
     "description": "업종을 고르고 주사위와 유행으로 실적이 정해진다", "expected_value": 760},
    {"id": "civil", "name": "공무원", "category": "밸런스", "requirements": {"지력": 45},
     "income": {"money": 70, "happiness": 3}, "pension": 80, "device": "",
     "description": "안정적이고 연금 80%", "expected_value": 700},
    {"id": "freelancer", "name": "프리랜서", "category": "행복 우선", "requirements": {},
     "income": {"money": 25, "happiness": 5}, "pension": 50, "device": "gig",
     "description": "누구나 가능. 바퀴마다 의뢰를 골라 큰돈을 노린다", "expected_value": 730,
     "pension_income": {"money": 55, "happiness": 5}},
    {"id": "artist", "name": "예술가", "category": "행복 우선", "requirements": {"센스": 60},
     "income": {"money": 0, "happiness": 9}, "pension": 50, "device": "artwork",
     "description": "돈은 작품을 팔아야 생긴다. 노년기 회고전", "expected_value": 760,
     "pension_income": {"money": 20, "happiness": 9}},
]

# 이벤트: effects는 크기 단어("+적당히", "-조금"). stage/job/kind로 고른다. student = 의대생 전용
EVENTS = [
    # 유아기
    {"id": "K-L1", "stage": "유아기", "kind": "luck", "name": "생일잔치", "effects": {"happiness": "+많이", "센스": "+조금"}, "text": "케이크에 촛불이 하나!"},
    {"id": "K-L2", "stage": "유아기", "kind": "luck", "name": "언어를 배웠다", "effects": {"happiness": "+적당히", "지력": "+적당히"}, "text": "첫 마디가 '엄마'가 아니라 '아빠'였다."},
    {"id": "K-L3", "stage": "유아기", "kind": "luck", "name": "놀이터 대장", "effects": {"happiness": "+조금", "체력": "+적당히"}, "text": "미끄럼틀 줄은 내가 정한다."},
    {"id": "K-B1", "stage": "유아기", "kind": "badluck", "name": "모바일 결제 버튼을 잘못 눌렀다", "effects": {"money": "-많이"}, "stat": "지력", "text": "게임 아이템이 50만원어치 생겼다."},
    {"id": "K-B2", "stage": "유아기", "kind": "badluck", "name": "좋아하는 인형이 사라졌다", "effects": {"happiness": "-적당히"}, "stat": "센스", "text": "세탁기 안에서 발견됐다..."},
    {"id": "K-B3", "stage": "유아기", "kind": "badluck", "name": "엄마한테 세뱃돈을 빼앗겼다", "effects": {"money": "-조금"}, "stat": "센스", "text": "\"엄마가 맡아 둘게.\""},
    # 청년기
    {"id": "Y-L1", "stage": "청년기", "kind": "luck", "name": "세뱃돈", "effects": {"money": "+많이"}, "text": "큰아버지가 지갑을 여셨다."},
    {"id": "Y-L2", "stage": "청년기", "kind": "luck", "name": "시험 잘 침", "effects": {"happiness": "+많이", "지력": "+적당히"}, "text": "찍은 게 다 맞았다."},
    {"id": "Y-L3", "stage": "청년기", "kind": "luck", "name": "맛도리 급식", "effects": {"happiness": "+조금", "체력": "+조금"}, "text": "오늘 급식은 돈가스다!"},
    {"id": "Y-B1", "stage": "청년기", "kind": "badluck", "name": "시험 망침", "effects": {"happiness": "-많이"}, "stat": "지력", "text": "밀린 인강이 300개."},
    {"id": "Y-B2", "stage": "청년기", "kind": "badluck", "name": "중고거래 사기", "effects": {"money": "-조금", "happiness": "-적당히"}, "stat": "센스", "text": "벽돌이 택배로 왔다."},
    {"id": "Y-B3", "stage": "청년기", "kind": "badluck", "name": "개학 전날", "effects": {"happiness": "-적당히"}, "stat": "체력", "text": "방학 숙제가 그대로다."},
    # 의대생 전용 (청년기 수치)
    {"id": "S-L1", "stage": "청년기", "job": "student", "kind": "luck", "name": "모의고사 전국 1등", "effects": {"happiness": "+적당히", "지력": "+적당히"}, "text": "엄마가 동네방네 자랑하고 다닌다."},
    {"id": "S-B1", "stage": "청년기", "job": "student", "kind": "badluck", "name": "옆집 애는 붙었다더라", "effects": {"happiness": "-적당히"}, "stat": "센스", "text": "명절마다 듣는 그 이름, 엄친아."},
    # 성년기·중년기 직업 이벤트 (일부)
    {"id": "D-A-L1", "stage": "성년기", "job": "doctor", "kind": "luck", "name": "당직 수당 두둑", "effects": {"money": "+적당히"}, "text": "주말 당직을 몰아 섰더니 통장이 든든하다."},
    {"id": "D-A-B1", "stage": "성년기", "job": "doctor", "kind": "badluck", "name": "36시간 연속 당직", "effects": {"happiness": "-적당히"}, "stat": "체력", "text": "눈 뜨고 자는 법을 터득했다..."},
    {"id": "D-M-B1", "stage": "중년기", "job": "doctor", "kind": "badluck", "name": "과로로 쓰러짐", "effects": {"happiness": "-적당히"}, "stat": "체력", "skip_turns": 1, "text": "의사도 환자가 될 수 있다. 1턴 쉰다."},
    {"id": "B-A-L1", "stage": "성년기", "job": "business", "kind": "luck", "name": "투자 유치 성공", "effects": {"money": "+적당히", "센스": "+조금"}, "text": "엔젤 투자자가 손을 내밀었다."},
    {"id": "B-A-B1", "stage": "성년기", "job": "business", "kind": "badluck", "name": "거래처 대금 미지급", "effects": {"money": "-적당히"}, "stat": "지력", "text": "계약서를 꼼꼼히 볼걸..."},
    {"id": "B-M-B1", "stage": "중년기", "job": "business", "kind": "badluck", "name": "세무조사", "effects": {"money": "-적당히"}, "stat": "지력", "text": "장부를 전부 들고 오라고 한다."},
    {"id": "C-A-L1", "stage": "성년기", "job": "civil", "kind": "luck", "name": "칼퇴 보장", "effects": {"happiness": "+적당히"}, "text": "6시 땡! 저녁이 있는 삶."},
    {"id": "C-A-B1", "stage": "성년기", "job": "civil", "kind": "badluck", "name": "악성 민원", "effects": {"happiness": "-적당히"}, "stat": "센스", "text": "같은 민원이 30번째 들어왔다."},
    {"id": "F-A-L1", "stage": "성년기", "job": "freelancer", "kind": "luck", "name": "출근 없는 아침", "effects": {"happiness": "+적당히"}, "text": "알람 없이 일어나 카페로 출근."},
    {"id": "F-A-B1", "stage": "성년기", "job": "freelancer", "kind": "badluck", "name": "무한 수정 요청", "effects": {"happiness": "-적당히"}, "stat": "체력", "text": "최종_진짜최종_이게진짜최종.psd"},
    {"id": "F-M-B1", "stage": "중년기", "job": "freelancer", "kind": "badluck", "name": "AI에게 일감 뺏김", "effects": {"money": "-조금"}, "stat": "지력", "text": "AI가 내 일을 10초 만에 끝냈다."},
    {"id": "A-A-L1", "stage": "성년기", "job": "artist", "kind": "luck", "name": "SNS 작품 바이럴", "effects": {"happiness": "+적당히", "센스": "+조금"}, "text": "작업 영상 조회수 100만 돌파!"},
    {"id": "A-A-B1", "stage": "성년기", "job": "artist", "kind": "badluck", "name": "작업실 월세 폭탄", "effects": {"money": "-적당히"}, "stat": "지력", "text": "건물주가 월세를 올렸다."},
    # 성년기·중년기 공통
    {"id": "X-L1", "stage": "성년기", "job": "common", "kind": "luck", "name": "결혼", "effects": {"happiness": "+많이"}, "special": "marry", "text": "평생 내 편이 생겼다."},
    {"id": "X-L2", "stage": "중년기", "job": "common", "kind": "luck", "name": "승진", "effects": {"happiness": "+조금"}, "special": "promote", "text": "매 턴 수입 +10%"},
    {"id": "X-B1", "stage": "성년기", "job": "common", "kind": "badluck", "name": "전세 사기", "effects": {"money": "-많이"}, "stat": "지력", "text": "집주인이 연락이 안 된다."},
    {"id": "X-B2", "stage": "중년기", "job": "common", "kind": "badluck", "name": "번아웃", "effects": {"happiness": "-많이"}, "stat": "체력", "text": "아무것도 하기 싫다."},
    # 노년기
    {"id": "O-L1", "stage": "노년기", "kind": "luck", "name": "트로트 가수 콘서트", "effects": {"happiness": "+적당히"}, "text": "형광봉을 흔들며 떼창했다."},
    {"id": "O-L2", "stage": "노년기", "kind": "luck", "name": "자녀가 용돈을 보냈다", "effects": {"money": "+적당히"}, "text": "\"엄마 아빠 맛있는 거 사 드세요.\""},
    {"id": "O-B1", "stage": "노년기", "kind": "badluck", "name": "틀니를 잃어버렸다", "effects": {"happiness": "-조금"}, "stat": "지력", "text": "강아지가 물고 갔다."},
    {"id": "O-B2", "stage": "노년기", "kind": "badluck", "name": "잔병치레", "effects": {"money": "-조금"}, "stat": "체력", "text": "병원 순례가 일과가 됐다."},
]

GOLDEN_KEYS = [   # count = 덱에 넣을 장수 (총 10장)
    {"id": "double_luck", "name": "행운 보상 2배", "keep": True, "count": 2, "description": "다음 행운 칸 효과 ×2"},
    {"id": "bad_to_good", "name": "불운→행운 변경권", "keep": True, "count": 2, "description": "불행 칸에서 쓰면 같은 단계 행운으로"},
    {"id": "lottery", "name": "복권", "keep": False, "count": 2, "description": "주사위 합 10 이상이면 돈 +많이"},
    {"id": "job_change", "name": "직업 변경권", "keep": True, "count": 1, "description": "출발 칸을 지날 때 직업을 바꿀 수 있다"},
    {"id": "invest_up", "name": "다음 투자 상승", "keep": True, "count": 2, "description": "다음 투자 배율 +0.5"},
    {"id": "blank", "name": "꽝", "keep": False, "count": 1, "description": "아무 일도 없었다"},
]

SHOP = [   # price·amount는 크기 단어 → 그 단계 수치표로 바꾼다
    {"id": "academy", "name": "학원", "price": "적당히", "stat": "지력", "amount": "적당히"},
    {"id": "gym", "name": "헬스장", "price": "적당히", "stat": "체력", "amount": "적당히"},
    {"id": "culture", "name": "문화생활", "price": "적당히", "stat": "센스", "amount": "적당히"},
    {"id": "insurance", "name": "보험", "price": "조금", "description": "다음 불행 1번 피해 50% 감소"},
    {"id": "lecture_pass", "name": "인강 패스", "price": "조금", "description": "다음 국가고시 제한 시간 +10초", "student_only": True},
]

COMPANIES = [
    {"id": "tuntun", "name": "튼튼전자", "type": "stable", "ratios_x10": [8, 9, 11, 13, 15]},
    {"id": "future_bio", "name": "미래바이오", "type": "growth", "ratios_x10": [3, 7, 12, 16, 25]},
    {"id": "hanbang", "name": "한방코인", "type": "gamble", "ratios_x10": [0, 2, 8, 25, 50]},
]

EXAM = [
    {"id": "D1-01", "level": 1, "question": "성인 몸의 뼈는 대략 몇 개인가?", "choices": ["106개", "206개", "306개", "406개"], "answer": 2},
    {"id": "D1-02", "level": 1, "question": "인슐린을 분비하는 장기는?", "choices": ["간", "쓸개", "이자(췌장)", "콩팥"], "answer": 3},
    {"id": "D2-01", "level": 2, "question": "혈액에서 산소를 운반하는 것은?", "choices": ["적혈구", "백혈구", "혈소판", "혈장"], "answer": 1},
    {"id": "D2-02", "level": 2, "question": "성인의 정상 안정 시 심박수(1분)는?", "choices": ["20~40회", "60~100회", "120~160회", "200회 이상"], "answer": 2},
    {"id": "D3-01", "level": 3, "question": "사람의 정상 체온에 가장 가까운 것은?", "choices": ["33도", "36.5도", "39도", "42도"], "answer": 2},
    {"id": "D3-02", "level": 3, "question": "비누로 손을 씻을 때 권장 시간은?", "choices": ["3초", "30초 이상", "5분", "1시간"], "answer": 2},
    {"id": "D4-01", "level": 4, "question": "병원에서 X-ray로 찍는 것은?", "choices": ["뼈", "꿈", "기억", "성적표"], "answer": 1},
    {"id": "D4-02", "level": 4, "question": "의사가 하는 말이 아닌 것은?", "choices": ["어디가 아프세요?", "아~ 해 보세요", "손님, 펌 하시겠어요?", "약 잘 챙겨 드세요"], "answer": 3},
    {"id": "D5-01", "level": 5, "question": "청진기로 듣는 것은?", "choices": ["심장·폐 소리", "라디오", "옆방 대화", "노래방 점수"], "answer": 1},
    {"id": "D5-02", "level": 5, "question": "병원에서 일하는 사람은?", "choices": ["의사", "해적", "마법사", "공룡"], "answer": 1},
]

BUSINESSES = [
    {"id": "store", "name": "스마트스토어", "kind": "안정형", "desc": "결과 폭이 좁고 꾸준하다",
     "table": [[0, -5], [700, 0], [900, 5], [1300, 10]], "trend_bonus": 1, "off_trend": 0},
    {"id": "youtube", "name": "유튜브 채널", "kind": "중간형", "desc": "알고리즘이 선택하면 대박",
     "table": [[-300, -10], [550, 0], [1250, 10], [2700, 30]], "trend_bonus": 1, "off_trend": 0},
    {"id": "nft", "name": "NFT 갤러리", "kind": "한 방형", "desc": "유행일 땐 대박, 아니면 적자",
     "table": [[-800, -20], [400, 0], [1500, 10], [3500, 30]], "trend_bonus": 3, "off_trend": -1},
]
TREND_HEADLINES = {   # [시작할 때, 끝날 때], {nft}에 NFT 이름
    "store": ["블랙프라이데이! 스마트스토어마다 주문 폭주", "세일이 끝났다... 반품 상자만 쌓인다"],
    "youtube": ["쇼츠 열풍! 알고리즘이 나를 선택했다, 조회수 100만", "알고리즘이 떠났다... 조회수 37회"],
    "nft": ["{nft} NFT가 10억에 팔렸다!", "NFT 거품 붕괴... 남은 건 {nft} 그림 JPG 한 장"],
    "none": ["이번 달은 조용하다. 사장님들의 한숨", ""],
}
NFT_NAMES = ["원숭이", "픽셀 얼굴", "펭귄", "돌멩이"]

GIGS = [
    {"id": "corp", "name": "대기업 외주", "quote": "로고를 크게, 그런데 작게 해 주세요.", "pay": 1000, "stars": 2,
     "risk": [2, 5], "stat": "체력", "accident": {"text": "수정 요청 47번째", "happiness": -50}},
    {"id": "jerk", "name": "진상 클라이언트", "quote": "이거 5분이면 하시잖아요?", "pay": 1400, "stars": 4,
     "risk": [2, 8], "stat": "지력", "accident": {"text": "잔금 받기 전에 잠수", "money": -700}},
    {"id": "abroad", "name": "해외 클라이언트", "quote": "Let's have a quick call at 3AM your time :)", "pay": 1200, "stars": 3,
     "risk": [2, 6], "stat": "체력", "accident": {"text": "시차 때문에 밤샘", "happiness": -70}},
    {"id": "friend", "name": "지인 찬스", "quote": "친구니까 싸게 해 줄 거지?", "pay": 400, "happiness": 30, "stars": 1,
     "risk": [2, 3], "stat": "센스", "accident": {"text": "친구 사이가 서먹해졌다", "happiness": -30}},
    {"id": "startup", "name": "열정페이 스타트업", "quote": "페이는 지분으로 드릴게요!", "pay": 200, "stars": 0,
     "jackpot": [11, 12], "bonus": {"text": "그 회사가 상장했다", "money": 3000}},
    {"id": "public", "name": "공공기관 용역", "quote": "서류는 원본으로 3부 제출해 주세요.", "pay": 800, "stars": 1,
     "risk": [2, 4], "stat": "지력", "accident": {"text": "도장 위치가 틀려 반려", "happiness": -20}},
    {"id": "youtuber", "name": "유튜버 외주", "quote": "썸네일에 화살표랑 놀란 얼굴 넣어 주세요.", "pay": 500, "happiness": 20, "stars": 1,
     "risk": [2, 3], "stat": "센스", "accident": {"text": "댓글창에 악플", "happiness": -20}},
    {"id": "free", "name": "무료 의뢰", "quote": "포트폴리오에 도움이 되실 거예요.", "pay": 0, "stats": {"센스": 3}, "stars": 0,
     "jackpot": [10, 12], "bonus": {"text": "입소문이 났다! 다음 의뢰 보수 2배", "double_next": True}},
]

ART = {
    "grades": [   # 작품 점수 = 주사위 합 + 센스 ÷ 20
        {"name": "망작", "min": 0, "price": 30, "text": "엄마만 좋아하는 그림이 나왔다."},
        {"name": "습작", "min": 7, "price": 100, "text": "연습이라고 생각하자."},
        {"name": "수작", "min": 10, "price": 300, "text": "SNS에 올렸더니 반응이 좋다."},
        {"name": "명작", "min": 13, "price": 800, "text": "붓을 놓는 순간 소름이 돋았다!"},
    ],
    "titles": ["월요일의 고뇌", "냉장고 속 우주", "퇴근 5분 전", "새벽 3시 라면", "카드값의 무게",
               "고양이가 밟고 간 캔버스", "알람을 끈 아침", "무제 (진짜 제목 없음)", "주말은 왜 짧은가",
               "택배를 기다리는 마음", "엄마의 잔소리 No.3", "적금 해지의 순간"],
}
