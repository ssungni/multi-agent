"""Mock 상품 카탈로그. 네이버 쇼핑 API 대체용 정적 데이터.

DB 테이블로 만들지 않은 이유: 이 카탈로그는 데모 기간 동안 바뀌지 않는
읽기 전용 데이터라 마이그레이션/시딩 스크립트를 둘 이유가 없음.
실 API 연동 시 이 리스트를 어댑터로 교체하면 됨.
"""

CATEGORIES = [
    "패션의류",
    "화장품/미용",
    "전자기기",
    "식품",
    "생활/주방용품",
    "스포츠/레저",
]

PRODUCTS = [
    # 패션의류
    {"id": 1, "name": "오버핏 코튼 반팔 티셔츠", "category": "패션의류", "brand": "무신사 스탠다드", "price": 19900, "stock": 120, "rating": 4.6, "review_count": 3120, "tags": ["티셔츠", "반팔", "여름", "베이직", "남녀공용"]},
    {"id": 2, "name": "슬림핏 스트레이트 데님 팬츠", "category": "패션의류", "brand": "리바이스", "price": 79000, "stock": 45, "rating": 4.4, "review_count": 1890, "tags": ["청바지", "데님", "슬림핏", "남성"]},
    {"id": 3, "name": "경량 후드 집업 자켓", "category": "패션의류", "brand": "노스페이스", "price": 129000, "stock": 30, "rating": 4.7, "review_count": 2210, "tags": ["자켓", "후드", "아우터", "간절기"]},
    {"id": 4, "name": "니트 가디건", "category": "패션의류", "brand": "8seconds", "price": 45900, "stock": 60, "rating": 4.3, "review_count": 980, "tags": ["가디건", "니트", "여성", "가을"]},
    {"id": 5, "name": "플리츠 미디 스커트", "category": "패션의류", "brand": "자라", "price": 39900, "stock": 80, "rating": 4.2, "review_count": 640, "tags": ["스커트", "플리츠", "여성", "오피스룩"]},
    {"id": 6, "name": "다운 롱 패딩", "category": "패션의류", "brand": "노스페이스", "price": 259000, "stock": 15, "rating": 4.8, "review_count": 4310, "tags": ["패딩", "겨울", "아우터", "방한"]},
    {"id": 7, "name": "런닝 반바지", "category": "패션의류", "brand": "나이키", "price": 34900, "stock": 100, "rating": 4.5, "review_count": 1520, "tags": ["반바지", "운동복", "런닝", "여름"]},
    {"id": 8, "name": "울 블렌드 코트", "category": "패션의류", "brand": "자라", "price": 189000, "stock": 20, "rating": 4.4, "review_count": 760, "tags": ["코트", "겨울", "아우터", "포멀"]},
    {"id": 9, "name": "스트라이프 셔츠", "category": "패션의류", "brand": "무신사 스탠다드", "price": 29900, "stock": 90, "rating": 4.1, "review_count": 430, "tags": ["셔츠", "스트라이프", "캐주얼"]},
    {"id": 10, "name": "레깅스 요가팬츠", "category": "패션의류", "brand": "안다르", "price": 42000, "stock": 150, "rating": 4.6, "review_count": 5200, "tags": ["레깅스", "요가", "운동복", "여성"]},

    # 화장품/미용
    {"id": 11, "name": "수분 진정 크림", "category": "화장품/미용", "brand": "닥터자르트", "price": 38000, "stock": 200, "rating": 4.7, "review_count": 8900, "tags": ["크림", "보습", "진정", "스킨케어"]},
    {"id": 12, "name": "선크림 SPF50+", "category": "화장품/미용", "brand": "라운드랩", "price": 18500, "stock": 300, "rating": 4.5, "review_count": 6700, "tags": ["선크림", "자외선차단", "여름", "스킨케어"]},
    {"id": 13, "name": "쿠션 파운데이션", "category": "화장품/미용", "brand": "헤라", "price": 42000, "stock": 90, "rating": 4.4, "review_count": 3400, "tags": ["쿠션", "베이스메이크업", "파운데이션"]},
    {"id": 14, "name": "립틴트 벨벳", "category": "화장품/미용", "brand": "롬앤", "price": 9900, "stock": 400, "rating": 4.6, "review_count": 12000, "tags": ["립틴트", "립메이크업", "가성비"]},
    {"id": 15, "name": "클렌징 오일", "category": "화장품/미용", "brand": "이니스프리", "price": 15900, "stock": 180, "rating": 4.3, "review_count": 5100, "tags": ["클렌징", "메이크업제거", "스킨케어"]},
    {"id": 16, "name": "헤어 에센스", "category": "화장품/미용", "brand": "미장센", "price": 12900, "stock": 220, "rating": 4.2, "review_count": 2900, "tags": ["헤어케어", "에센스", "손상모"]},
    {"id": 17, "name": "비타민C 세럼", "category": "화장품/미용", "brand": "닥터자르트", "price": 45000, "stock": 70, "rating": 4.5, "review_count": 4200, "tags": ["세럼", "미백", "비타민C", "스킨케어"]},
    {"id": 18, "name": "마스카라 롱래쉬", "category": "화장품/미용", "brand": "클리오", "price": 16900, "stock": 150, "rating": 4.3, "review_count": 3300, "tags": ["마스카라", "아이메이크업"]},
    {"id": 19, "name": "바디로션 시어버터", "category": "화장품/미용", "brand": "니베아", "price": 11900, "stock": 250, "rating": 4.1, "review_count": 1800, "tags": ["바디로션", "보습", "겨울"]},
    {"id": 20, "name": "향수 오드퍼퓸 50ml", "category": "화장품/미용", "brand": "딥티크", "price": 189000, "stock": 25, "rating": 4.8, "review_count": 1200, "tags": ["향수", "퍼퓸", "선물"]},

    # 전자기기
    {"id": 21, "name": "무선 블루투스 이어폰", "category": "전자기기", "brand": "삼성", "price": 159000, "stock": 60, "rating": 4.5, "review_count": 9800, "tags": ["이어폰", "블루투스", "무선", "음향기기"]},
    {"id": 22, "name": "노이즈캔슬링 헤드폰", "category": "전자기기", "brand": "소니", "price": 349000, "stock": 25, "rating": 4.7, "review_count": 4300, "tags": ["헤드폰", "노이즈캔슬링", "음향기기"]},
    {"id": 23, "name": "보조배터리 20000mAh", "category": "전자기기", "brand": "앤커", "price": 39900, "stock": 200, "rating": 4.6, "review_count": 7600, "tags": ["보조배터리", "충전", "휴대용"]},
    {"id": 24, "name": "게이밍 무선 마우스", "category": "전자기기", "brand": "로지텍", "price": 69000, "stock": 80, "rating": 4.6, "review_count": 3200, "tags": ["마우스", "게이밍", "무선"]},
    {"id": 25, "name": "스마트워치", "category": "전자기기", "brand": "애플", "price": 459000, "stock": 40, "rating": 4.7, "review_count": 6100, "tags": ["스마트워치", "웨어러블", "건강관리"]},
    {"id": 26, "name": "usb-c 멀티허브", "category": "전자기기", "brand": "앤커", "price": 45000, "stock": 110, "rating": 4.4, "review_count": 2100, "tags": ["허브", "usb-c", "노트북액세서리"]},
    {"id": 27, "name": "27인치 모니터 IPS", "category": "전자기기", "brand": "LG", "price": 279000, "stock": 20, "rating": 4.5, "review_count": 1900, "tags": ["모니터", "IPS", "사무용"]},
    {"id": 28, "name": "기계식 키보드", "category": "전자기기", "brand": "로지텍", "price": 129000, "stock": 55, "rating": 4.4, "review_count": 2800, "tags": ["키보드", "기계식", "게이밍"]},
    {"id": 29, "name": "휴대용 미니 선풍기", "category": "전자기기", "brand": "샤오미", "price": 15900, "stock": 300, "rating": 4.0, "review_count": 4400, "tags": ["선풍기", "여름", "휴대용"]},
    {"id": 30, "name": "웹캠 1080p", "category": "전자기기", "brand": "로지텍", "price": 55000, "stock": 65, "rating": 4.3, "review_count": 1300, "tags": ["웹캠", "화상회의", "재택근무"]},

    # 식품
    {"id": 31, "name": "왕뚜껑 컵라면 5입", "category": "식품", "brand": "팔도", "price": 4980, "stock": 500, "rating": 4.5, "review_count": 8200, "tags": ["라면", "컵라면", "간편식"]},
    {"id": 32, "name": "제주 삼다수 2L 6입", "category": "식품", "brand": "삼다수", "price": 7900, "stock": 600, "rating": 4.7, "review_count": 5400, "tags": ["생수", "물", "생필품"]},
    {"id": 33, "name": "곰곰 무항생제 계란 30구", "category": "식품", "brand": "곰곰", "price": 9900, "stock": 150, "rating": 4.6, "review_count": 3900, "tags": ["계란", "신선식품"]},
    {"id": 34, "name": "즉석밥 백미 24개입", "category": "식품", "brand": "햇반", "price": 19900, "stock": 200, "rating": 4.6, "review_count": 6700, "tags": ["즉석밥", "간편식", "쌀"]},
    {"id": 35, "name": "그릭요거트 무가당 4입", "category": "식품", "brand": "동원", "price": 8900, "stock": 90, "rating": 4.3, "review_count": 1500, "tags": ["요거트", "유제품", "다이어트"]},
    {"id": 36, "name": "원두커피 홀빈 1kg", "category": "식품", "brand": "테라로사", "price": 24900, "stock": 70, "rating": 4.8, "review_count": 2100, "tags": ["커피", "원두", "음료"]},
    {"id": 37, "name": "저당 프로틴바 12입", "category": "식품", "brand": "밀박스", "price": 21900, "stock": 130, "rating": 4.2, "review_count": 1700, "tags": ["프로틴바", "다이어트", "간식"]},
    {"id": 38, "name": "냉동 만두 왕교자 1kg", "category": "식품", "brand": "비비고", "price": 12900, "stock": 180, "rating": 4.5, "review_count": 4600, "tags": ["만두", "냉동식품", "간편식"]},
    {"id": 39, "name": "제주 감귤 3kg", "category": "식품", "brand": "농협", "price": 15900, "stock": 60, "rating": 4.4, "review_count": 980, "tags": ["과일", "감귤", "신선식품"]},
    {"id": 40, "name": "견과류 믹스 500g", "category": "식품", "brand": "곰곰", "price": 13900, "stock": 140, "rating": 4.3, "review_count": 1200, "tags": ["견과류", "간식", "건강식품"]},

    # 생활/주방용품
    {"id": 41, "name": "스테인리스 텀블러 500ml", "category": "생활/주방용품", "brand": "락앤락", "price": 15900, "stock": 200, "rating": 4.5, "review_count": 3300, "tags": ["텀블러", "보온보냉", "주방용품"]},
    {"id": 42, "name": "IH 인덕션 프라이팬 세트", "category": "생활/주방용품", "brand": "테팔", "price": 89000, "stock": 40, "rating": 4.6, "review_count": 2400, "tags": ["프라이팬", "주방용품", "인덕션"]},
    {"id": 43, "name": "무선 핸디 청소기", "category": "생활/주방용품", "brand": "다이슨", "price": 399000, "stock": 15, "rating": 4.7, "review_count": 1900, "tags": ["청소기", "무선", "생활가전"]},
    {"id": 44, "name": "극세사 극세모 이불", "category": "생활/주방용품", "brand": "이케아", "price": 49900, "stock": 55, "rating": 4.3, "review_count": 870, "tags": ["침구", "이불", "겨울"]},
    {"id": 45, "name": "다용도 밀폐용기 10종 세트", "category": "생활/주방용품", "brand": "락앤락", "price": 32900, "stock": 100, "rating": 4.5, "review_count": 2600, "tags": ["밀폐용기", "주방용품", "수납"]},
    {"id": 46, "name": "가습기 초음파식", "category": "생활/주방용품", "brand": "샤오미", "price": 45900, "stock": 60, "rating": 4.2, "review_count": 1500, "tags": ["가습기", "생활가전", "겨울"]},
    {"id": 47, "name": "극세사 욕실 매트", "category": "생활/주방용품", "brand": "무인양품", "price": 12900, "stock": 130, "rating": 4.1, "review_count": 640, "tags": ["욕실용품", "매트"]},
    {"id": 48, "name": "원목 도마 세트", "category": "생활/주방용품", "brand": "이케아", "price": 22900, "stock": 80, "rating": 4.4, "review_count": 590, "tags": ["도마", "주방용품"]},
    {"id": 49, "name": "공기청정기 소형", "category": "생활/주방용품", "brand": "샤오미", "price": 129000, "stock": 30, "rating": 4.5, "review_count": 2200, "tags": ["공기청정기", "생활가전"]},
    {"id": 50, "name": "전기포트 1.7L", "category": "생활/주방용품", "brand": "필립스", "price": 29900, "stock": 90, "rating": 4.3, "review_count": 1100, "tags": ["전기포트", "주방가전"]},

    # 스포츠/레저
    {"id": 51, "name": "요가매트 10mm", "category": "스포츠/레저", "brand": "데카트론", "price": 25900, "stock": 120, "rating": 4.5, "review_count": 3100, "tags": ["요가매트", "운동", "홈트"]},
    {"id": 52, "name": "런닝화 쿠셔닝", "category": "스포츠/레저", "brand": "나이키", "price": 139000, "stock": 45, "rating": 4.6, "review_count": 5600, "tags": ["런닝화", "운동화", "런닝"]},
    {"id": 53, "name": "폴딩 캠핑 의자", "category": "스포츠/레저", "brand": "코베아", "price": 59000, "stock": 35, "rating": 4.4, "review_count": 1400, "tags": ["캠핑", "의자", "아웃도어"]},
    {"id": 54, "name": "덤벨 세트 20kg", "category": "스포츠/레저", "brand": "데카트론", "price": 79000, "stock": 25, "rating": 4.5, "review_count": 890, "tags": ["덤벨", "헬스", "홈트"]},
    {"id": 55, "name": "자전거 헬멧", "category": "스포츠/레저", "brand": "지로", "price": 89000, "stock": 30, "rating": 4.6, "review_count": 620, "tags": ["헬멧", "자전거", "안전용품"]},
    {"id": 56, "name": "등산 스틱 2p", "category": "스포츠/레저", "brand": "블랙야크", "price": 45900, "stock": 40, "rating": 4.3, "review_count": 780, "tags": ["등산", "스틱", "아웃도어"]},
    {"id": 57, "name": "텐트 4인용", "category": "스포츠/레저", "brand": "코베아", "price": 259000, "stock": 12, "rating": 4.7, "review_count": 1100, "tags": ["텐트", "캠핑", "아웃도어"]},
    {"id": 58, "name": "축구공 5호", "category": "스포츠/레저", "brand": "나이키", "price": 34900, "stock": 70, "rating": 4.4, "review_count": 990, "tags": ["축구공", "구기종목"]},
    {"id": 59, "name": "수영 고글", "category": "스포츠/레저", "brand": "스피도", "price": 19900, "stock": 100, "rating": 4.2, "review_count": 1600, "tags": ["수영", "고글", "수영용품"]},
    {"id": 60, "name": "폼롤러 마사지", "category": "스포츠/레저", "brand": "데카트론", "price": 18900, "stock": 110, "rating": 4.3, "review_count": 2000, "tags": ["폼롤러", "스트레칭", "홈트"]},
]
