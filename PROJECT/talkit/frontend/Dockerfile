# ── base: 의존성 설치 ─────────────────────────────────────────────
FROM node:20-alpine AS base
WORKDIR /app
COPY package.json ./
RUN npm install

# ── dev: docker-compose 기본 타겟 (Vite dev server + HMR) ──────────
FROM base AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ── build: 정적 자산 빌드 ──────────────────────────────────────────
FROM base AS build
COPY . .
RUN npm run build

# ── production: nginx로 정적 자산 서빙 + /api 리버스 프록시 ─────────
FROM nginx:alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
