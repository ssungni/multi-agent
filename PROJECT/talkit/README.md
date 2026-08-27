# talkit(AI 음성 기반 영어 회화 서비스) 프로젝트

- Basic (1 가능)
- Premium (1, 2, 3 가능)

```bash
(1) 토픽: 글을 읽으며 영어 표현을 익힐 수 있는 공간
(2) AI 튜터: 관심 주제를 골라 AI와 대화하며 연습/실전 모드로 대화할 수 있는 공간
(3) AI 롤플레이: 실생활 시나리오를 연습/실전 모드로 음성 대화 가능
```

---

## 실행

```bash
cp .env.example .env        # OPENAI_API_KEY 등 값 채우기
docker compose up --build
```


| 서비스   | 접속 주소             | 설명                                                           |
| -------- | --------------------- | -------------------------------------------------------------- |
| frontend | http://localhost:5173 | Vite dev server                                                |
| backend  | http://localhost:3000 | Rails API (최초 기동 시 DB 생성/마이그레이션 + 시드 자동 등록) |
| db       | localhost:5432        | PostgreSQL 16                                                  |

Docker 없이 로컬에서 직접 실행하려면:

```bash
# Backend (Ruby 3.3 / Rails 7.1 / PostgreSQL 14+)
cd backend
bundle install
export OPENAI_API_KEY=sk-...
rails db:create db:migrate db:seed
rails server -p 3000

# Frontend (Node 18+)
cd frontend
npm install
npm run dev
```

---

## API

**공통**: Base URL `/api/v1` · 유저 인증 `X-User-Id` 헤더 · Admin 인증 `X-Admin-Token` 헤더


| Method | Endpoint                 | 인증                      | 설명                      |
| ------ | ------------------------ | ------------------------- | ------------------------- |
| GET    | `/membership_plans`      | -                         | 활성 플랜 목록            |
| GET    | `/me/membership`         | User                      | 내 활성 멤버십 조회       |
| POST   | `/payments`              | User                      | 멤버십 결제 (Mock PG)     |
| GET    | `/admin/users`           | Admin                     | 유저 목록 + 멤버십 현황   |
| POST   | `/admin/memberships`     | Admin                     | 멤버십 강제 부여          |
| DELETE | `/admin/memberships/:id` | Admin                     | 멤버십 삭제 (soft delete) |
| POST   | `/conversations/chat`    | User +`conversation` 권한 | LLM 응답 스트리밍 (SSE)   |
| POST   | `/conversations/stt`     | User +`conversation` 권한 | 음성 → 텍스트 (Whisper)  |
| POST   | `/conversations/tts`     | User +`conversation` 권한 | 텍스트 → 음성 (TTS-1)    |

---

## 기술 스택

- **Backend**: Rails 7.1 (API mode), PostgreSQL, rack-attack, ruby-openai
- **Frontend**: React 18 + TypeScript, Vite, Zustand, TanStack Query, shadcn/ui + Tailwind

---

## 테스트

```bash
cd backend
bundle exec rspec
```
