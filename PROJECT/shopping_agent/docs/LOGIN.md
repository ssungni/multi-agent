# 회원가입 / 로그인 구현 정리

FastAPI + SQLAlchemy 2.x + PostgreSQL + Redis + JWT 기반으로 구현한 회원 시스템 정리 문서. 설계 배경은 대화 로그 참고, 여기서는 최종 구현 상태 + 실행 방법 + 테스트 시나리오만 다룬다.

## 1. 구현 범위

| 레이어 | 파일 | 내용 |
|---|---|---|
| Model | `backend/src/auth/models.py` | `users` 테이블 (ERD 그대로: email은 `CITEXT`, status는 CHECK 제약) |
| Schema | `backend/src/auth/schemas.py` | 요청/응답 Pydantic 모델 + 비밀번호/전화번호 validator |
| Repository | `backend/src/auth/repository.py` | `UserRepository` — DB 쿼리만 담당, 커밋은 `get_db()`가 요청 단위로 처리 |
| Service | `backend/src/auth/service.py` | `AuthService` — 회원가입/인증/로그인/토큰갱신/로그아웃 비즈니스 로직 |
| Router | `backend/src/auth/router.py` | 9개 엔드포인트 |
| 예외 | `backend/src/auth/exceptions.py` + `backend/src/exceptions.py` | 도메인 예외 → `{error_code, message}` JSON으로 매핑하는 전역 핸들러 |
| Entry | `backend/src/main.py` | FastAPI 앱, CORS, lifespan(citext extension + 테이블 생성) |

**구현 안 한 것 (의도적 보류)**
- 실제 SMTP 발송 — 지금은 인증코드를 서버 콘솔 로그로만 출력 (`src/auth/email_service.py`). 실제 발송 필요해지면 이 파일만 교체.
- Rate limiting 미들웨어 — Redis 카운터(로그인 실패, 재발송 쿨다운)로 최소한의 방어만 있고, IP 단위 rate limit은 아직 없음.
- Alembic 마이그레이션 — 앱 시작 시 `Base.metadata.create_all`로 테이블을 자동 생성 (README에 명시된 초기 단계 방식 유지).
- 프론트엔드 — `frontend/`는 아직 빈 디렉토리. 아래 4번은 React 코드 작성 시 참고할 입력 시나리오만 정리.

## 2. 실행 방법

### 2-1. 의존 서비스 (Postgres, Redis)

```bash
docker run --rm -d --name cartmate-dev-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=cartmate -p 5432:5432 postgres:16
docker run --rm -d --name cartmate-dev-redis -p 6379:6379 redis:7
```

`backend/.env`의 `DATABASE_URL`이 이 값(`postgresql+psycopg2://postgres:postgres@localhost:5432/cartmate`)을 그대로 가리키고 있으면 별도 설정 불필요. `citext` extension과 테이블은 서버 기동 시 자동 생성됨.

### 2-2. 백엔드 서버

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- 헬스체크: http://localhost:8000/health

### 2-3. 테스트

`tests/auth/conftest.py`가 `localhost:5433`의 별도 테스트 DB를 사용한다(개발 DB와 섞이지 않도록 분리). 최초 1회만 띄워두면 됨:

```bash
docker run --rm -d --name cartmate-test-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=cartmate_test -p 5433:5432 postgres:16
cd backend
pytest tests/ -v
```

Redis는 테스트에서 `fakeredis`(인메모리)로 대체하므로 별도 컨테이너 불필요. 총 42개 테스트(model/schema/repository/service/router) 통과 확인됨.

## 3. Swagger UI 테스트 시나리오

http://localhost:8000/docs 에서 아래 순서대로 "Try it out"으로 실행.

### Step 1 — 회원가입 `POST /api/auth/signup`

```json
{
  "name": "테스터",
  "email": "tester@example.com",
  "password": "Test1234!",
  "phone": "010-2222-3333"
}
```
기대 결과: `201`, `{"message": "...", "email": "tester@example.com"}`

인증코드는 실제 메일이 아니라 **백엔드 서버를 실행 중인 터미널 콘솔**에 로그로 찍힌다:
```
INFO:src.auth.email_service:[mock email] 인증코드 발송 → tester@example.com : 123456
```
이 6자리 숫자를 다음 단계에 사용.

### Step 2 — 이메일 인증 `POST /api/auth/signup/verify`

```json
{ "email": "tester@example.com", "code": "123456" }
```
기대 결과: `200`, `access_token` 반환 + 응답 헤더에 `Set-Cookie: refresh_token=...` (Swagger UI 네트워크 탭에서 확인 가능. 브라우저가 자동으로 쿠키 저장하므로 이후 `/refresh`, `/logout` 요청에 자동으로 실림)

### Step 3 — 인증된 요청 테스트 `GET /api/users/me`

Swagger UI 우측 상단 **Authorize** 버튼 클릭 → Step 2에서 받은 `access_token` 값을 붙여넣기 → `GET /api/users/me` 실행.
기대 결과: `200`, 가입한 유저 정보(`status: "ACTIVE"`) 반환.

### Step 4 — 로그인 `POST /api/auth/login`

```json
{ "email": "tester@example.com", "password": "Test1234!" }
```
기대 결과: `200`, 새 `access_token` 발급.

### Step 5 — 토큰 재발급 `POST /api/auth/refresh`

바디 없이 그냥 실행 (쿠키가 자동으로 전달됨). 기대 결과: `200`, 새 `access_token`. 이때 이전 refresh token은 무효화되므로 **한 번 더 `/refresh`를 누르면 새로 받은 쿠키 기준으로는 성공, 이전 쿠키를 수동으로 넣어 재사용하면 `401 INVALID_REFRESH_TOKEN`**이어야 함(회전 확인용).

### Step 6 — 로그아웃 `POST /api/auth/logout`

바디 없이 실행. 이후 `/api/auth/refresh`를 다시 호출하면 `401 INVALID_REFRESH_TOKEN`이 떠야 정상(쿠키가 무효화됨).

### 예외 케이스도 같이 테스트해볼 것

| 시나리오 | 요청 | 기대 응답 |
|---|---|---|
| 이메일 중복 가입 | 위에서 이미 인증 완료한 `tester@example.com`으로 다시 `/signup` | `409 EMAIL_DUPLICATE` |
| 비밀번호 정책 위반 | `password: "weak"`로 `/signup` | `422` (Pydantic validation) |
| 전화번호 형식 오류 | `phone: "01012345"`로 `/signup` | `422` |
| 잘못된 인증코드 | `/signup/verify`에 임의의 `"000000"` 입력 | `400 VERIFY_CODE_MISMATCH` (5회 틀리면 코드 폐기, 이후 `400 VERIFY_CODE_EXPIRED`) |
| 미인증 계정 로그인 | 인증 안 한 이메일로 `/login` | `403 EMAIL_NOT_VERIFIED` |
| 잘못된 비밀번호 로그인 5회 | `/login`에 틀린 비밀번호로 5번 반복 | 5번째까지 `401 INVALID_CREDENTIALS`, 6번째부터 `423 ACCOUNT_LOCKED` |
| 토큰 없이 `/users/me` | Authorize 없이 실행 | `401 INVALID_ACCESS_TOKEN` |
| 이메일/전화번호 중복 확인 | `GET /api/auth/check-email?email=tester@example.com` | `{"available": false}` (이미 ACTIVE) |

## 4. 프론트엔드(React) 테스트 시나리오

`frontend/`는 아직 코드가 없는 상태 — 이전에 설계한 `SignupPage → VerifyEmailPage → LoginPage` 흐름을 구현한 뒤 아래 값으로 직접 눌러보면서 확인하면 됨.

| 화면 | 입력 | 기대 UI 동작 |
|---|---|---|
| 회원가입 폼 | 이름 `테스터`, 이메일 `tester2@example.com`, 비밀번호 `Test1234!`, 전화번호 `010-3333-4444` | 제출 시 `/signup/verify` 페이지로 이동, "인증코드를 발송했습니다" 안내 |
| 회원가입 폼 — 실시간 중복확인 | 이메일 입력란에 `tester@example.com` 입력 후 포커스 아웃 | `check-email` 호출 → "이미 사용 중인 이메일입니다" 필드 에러 표시 |
| 회원가입 폼 — 약한 비밀번호 | 비밀번호에 `1234` 입력 | 서버 호출 전에 클라이언트 validation으로 즉시 에러 표시(길이/복잡도) |
| 이메일 인증 화면 | 백엔드 콘솔 로그에서 확인한 6자리 코드 입력 | 성공 시 access token 저장 + 홈으로 리다이렉트(자동 로그인) |
| 이메일 인증 화면 — 오입력 | 임의의 `000000` 입력 | "인증코드가 일치하지 않습니다" 에러, 재발송 버튼 활성 유지 |
| 로그인 폼 | 이메일 `tester@example.com`, 비밀번호 `Test1234!` | 성공 시 홈으로 이동, 새로고침해도 로그인 유지되는지 확인(silent refresh) |
| 로그인 폼 — 틀린 비밀번호 | 비밀번호에 `WrongPass1!` 입력 | "이메일 또는 비밀번호가 올바르지 않습니다" 에러 (계정 존재 여부 노출 안 됨) |
| 로그아웃 | 홈 화면에서 로그아웃 버튼 | 홈 접근 시 `/login`으로 리다이렉트되는지 확인 (ProtectedRoute 동작 확인) |

프론트에서 백엔드를 호출하려면 `backend/.env`의 `FRONTEND_ORIGIN`이 프론트 개발 서버 주소(`http://localhost:3000`)와 일치해야 CORS가 통과되고, axios는 `withCredentials: true`로 설정해야 refresh token 쿠키가 오간다.
