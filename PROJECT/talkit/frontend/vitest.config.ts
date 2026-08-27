import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    globals: false,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/main.tsx',
        'src/App.tsx', // 라우트 정의만 있는 조립 코드 — 페이지와 동일하게 단위 테스트 대상에서 제외
        'src/test/**',
        'src/**/*.d.ts',
        'src/types/**', // 타입 전용 — 런타임 코드 없음
        'src/components/ui/**', // shadcn/ui 프리미티브 — 외부 라이브러리 래퍼, 자체 로직 없음
        'src/lib/queryClient.ts', // TanStack Query 기본 설정 객체 — 분기 없음
        // 페이지 단위 통합 시나리오는 Unit이 아닌 MSW 기반 Integration 테스트로 별도 커버한다
        // (docs/02_architecture.md §9.3 — Unit/Integration 레이어 분리)
        'src/pages/**',
        // 실제 디바이스 API(MediaRecorder/getUserMedia, Canvas rAF 루프)에 강하게 결합되어
        // 의미 있는 단위 테스트보다 E2E/수동 QA가 더 적합한 영역
        'src/hooks/useAudioRecorder.ts',
        'src/hooks/useWaveform.ts',
        'src/hooks/useVAD.ts',
        'src/hooks/useConversation.ts', // 위 훅들을 조합하는 오케스트레이터 — 통합 테스트 대상
        'src/components/chat/Waveform.tsx',
      ],
      thresholds: {
        lines: 80,
        statements: 80,
        functions: 75,
        branches: 70,
      },
    },
  },
})
