import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// Docker 환경에서는 backend가 별도 컨테이너(서비스명 "backend")로 존재하므로
// docker-compose가 VITE_API_PROXY_TARGET=http://backend:3000 으로 덮어쓴다.
// 로컬 실행 시 기본값은 "localhost" 대신 "127.0.0.1"을 명시한다 — Node가 localhost를
// IPv6(::1)로 먼저 해석할 때, Docker Desktop의 포트포워딩이 IPv6 루프백을 제대로
// 컨테이너로 연결하지 못해 ECONNRESET이 나는 환경이 있다 (127.0.0.1은 항상 IPv4로 고정).
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:3000'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true, // 0.0.0.0 바인딩 — 컨테이너 외부(호스트)에서 접근 가능하도록
    port: 5173,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
})
