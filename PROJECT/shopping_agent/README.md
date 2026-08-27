# CartMate

AI 이커머스 에이전트 학습 프로젝트. FastAPI + LangGraph + LangChain + LangSmith 백엔드, Next.js 프론트엔드.

설계 전체는 Notion 문서 참고: [CartMate — 이커머스 에이전트 제안서](https://app.notion.com/p/3ac3d7d94f9881e8bc64e80e46db9ef0)

현재 구현 범위: 로드맵 0단계(인증) + 1단계(구매자 대화형 쇼핑 어시스턴트 + 장바구니 + mock 결제). 2단계 이후(환불/CS, 가격 인텔리전스, 이미지/영상 에이전트 등)는 아직 미구현.

## 아키텍처 요약

- 에이전트 그래프: `extract_intent → search_products → (결과 없으면 1회 재질의) → rank_and_respond → add_to_cart`
- `add_to_cart`는 상태를 바꾸는 액션이라 LangGraph `interrupt()`로 멈춰서 프론트의 확인(버튼 클릭)을 기다리는 human-in-the-loop 패턴
- 인증: NextAuth.js(이메일/비밀번호 + Google)가 로그인 UI를 담당하고, 로그인 성공 시 FastAPI가 발급한 자체 JWT(`backendToken`)를 세션에 실어 API 호출에 사용. NextAuth의 세션 토큰 자체를 FastAPI가 검증하는 대신, FastAPI가 토큰 발급의 단일 소스가 되도록 단순화함 (Notion 문서의 "동일 시크릿 공유" 설계보다 구현이 단순하고 NextAuth 내부 암호화 포맷에 의존하지 않음)

## 사전 준비물

1. **PostgreSQL** — 로컬에 설치하거나 Docker로 실행: `docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres`, 이후 `cartmate` 데이터베이스 생성
2. **Anthropic API 키** — https://console.anthropic.com
3. **네이버 쇼핑 검색 API** (선택) — https://developers.naver.com/apps 에서 애플리케이션 생성 후 **"검색" API를 반드시 추가**해야 함 (안 하면 401 "Scope Status Invalid" 에러). 키가 없으면 목(mock) 상품 데이터로 자동 대체되어 데모는 계속 가능.
4. **Google OAuth 클라이언트** (선택, 구글 로그인용) — https://console.cloud.google.com/apis/credentials 에서 OAuth 클라이언트 ID 생성, 승인된 리디렉션 URI에 `http://localhost:3000/api/auth/callback/google` 추가

## 백엔드 실행

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # 값 채우기
uvicorn app.main:app --reload
```

- 헬스체크: `curl http://localhost:8000/health`
- 테스트: `pytest`
- 앱 시작 시 테이블을 자동 생성합니다(Alembic 마이그레이션 없음 — 초기 단계라 의도적으로 생략).

## 프론트엔드 실행

```bash
cd frontend
npm install
cp .env.example .env.local   # 값 채우기, NEXTAUTH_SECRET은 아무 랜덤 문자열
npm run dev
```

http://localhost:3000 접속 → `/signup`으로 이메일 회원가입 → `/chat`에서 예시 질문 클릭 또는 직접 입력.

## 알려진 제약

- 프론트엔드 의존성(Next.js 14.x)에 `npm audit`이 잡아내는 CVE가 여러 건 있습니다(대부분 self-hosted 프로덕션 배포에 해당하는 DoS/SSRF 계열). Next 16으로 올리면 해결되지만 next-auth v4와의 호환성이 검증되지 않아 이번 범위에서는 보류했습니다. 실제 배포 전에는 Next 15/16 + Auth.js v5 마이그레이션을 검토하세요.
- Mock 결제이므로 실제 PG 연동이 아닙니다. 카드 번호가 "0000"으로 끝나면 결제 실패를 재현합니다.
- LangGraph의 `MemorySaver` 체크포인터는 프로세스 메모리에만 저장되므로, 서버를 재시작하면 진행 중이던 장바구니 확인(interrupt) 상태가 사라집니다. 프로덕션에서는 영속 체크포인터로 교체해야 합니다.
