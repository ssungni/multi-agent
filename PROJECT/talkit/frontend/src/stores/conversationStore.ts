// AI 튜터 대화 세션의 상태(연습/실전 모드, 진행 상태, 메시지 목록, 스트리밍 중인 응답,
// 세션 시작 시각 등)를 관리하는 핵심 스토어.
import { create } from 'zustand'
import type { ConversationMode, ConversationStatus, Message } from '@/types/conversation'

interface ConversationState {
  status: ConversationStatus
  messages: Message[]
  streamingContent: string
  error: string | null
  topicId: string
  // 롤플레이 시나리오 진입 시 백엔드(Ai::ChatService::TOPICS)가 내려준 오프닝 대사.
  // 시나리오 없이 들어온 자유대화(AI 튜터)에서는 null — 이때는 시간대 인사로 대체된다.
  scenarioOpening: string | null
  scenarioLiveOpening: string | null
  // 연습/실전 모드 — 모드 선택 화면에서 설정되고, 대화가 reset()되어도 유지된다
  // (대화 세션 시작/종료와는 별개의 선택이기 때문에 `initial`에 포함하지 않음).
  mode: ConversationMode
  // 이번 세션이 실제로 시작된 시각 — 세션 30분 한도 계산에 쓰인다. startOpening()에서 설정.
  sessionStartedAt: number | null
  setTopicId: (topicId: string) => void
  setScenarioOpenings: (opening: string | null, liveOpening: string | null) => void
  setMode: (mode: ConversationMode) => void
  markSessionStarted: () => void
  setStatus: (status: ConversationStatus) => void
  addMessage: (message: Message) => void
  appendStreamDelta: (delta: string) => void
  commitStreamMessage: (id: string) => void
  clearStreaming: () => void
  setError: (error: string) => void
  addAudioUrl: (messageId: string, audioUrl: string) => void
  reset: () => void
}

// reset() 시 되돌릴 기본 상태 — mode는 세션과 무관하게 유지되어야 하므로 여기 포함하지 않는다.
const initial = {
  status: 'idle' as ConversationStatus,
  messages: [] as Message[],
  streamingContent: '',
  error: null as string | null,
  topicId: 'general_english',
  scenarioOpening: null as string | null,
  scenarioLiveOpening: null as string | null,
  sessionStartedAt: null as number | null,
}

export const useConversationStore = create<ConversationState>((set) => ({
  ...initial,
  mode: 'practice',

  setTopicId: (topicId) => set({ topicId }),

  setScenarioOpenings: (opening, liveOpening) =>
    set({ scenarioOpening: opening, scenarioLiveOpening: liveOpening }),

  setMode: (mode) => set({ mode }),

  // 세션 30분 타이머의 기준 시각을 기록 (대화 시작 시점에 한 번 호출)
  markSessionStarted: () => set({ sessionStartedAt: Date.now() }),

  setStatus: (status) => set({ status }),

  addMessage: (message) => set((s) => ({ messages: [...s.messages, message] })),

  // LLM 응답이 토큰 단위로 들어올 때마다 누적해서 화면에 실시간으로 보여주기 위함
  appendStreamDelta: (delta) =>
    set((s) => ({ streamingContent: s.streamingContent + delta })),

  // 스트리밍이 끝난 응답을 하나의 완성된 메시지로 messages에 확정(commit)하고 스트리밍 버퍼는 비움
  commitStreamMessage: (id) =>
    set((s) => ({
      messages: [
        ...s.messages,
        { id, role: 'assistant', content: s.streamingContent, isStreaming: false },
      ],
      streamingContent: '',
    })),

  clearStreaming: () => set({ streamingContent: '' }),

  // 에러 발생 시 상태를 'error'로 전환하면서 에러 메시지도 함께 저장
  setError: (error) => set({ status: 'error', error }),

  // 한 메시지가 문장별로 여러 오디오 클립을 가질 수 있으므로 덮어쓰지 않고 순서대로 누적한다.
  addAudioUrl: (messageId, audioUrl) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === messageId ? { ...m, audioUrls: [...(m.audioUrls ?? []), audioUrl] } : m
      ),
    })),

  // 대화 세션 종료/재시작 시 진행 상태만 초기화 (mode는 유지)
  reset: () => set(initial),
}))
