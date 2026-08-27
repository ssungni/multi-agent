import '@testing-library/jest-dom/vitest'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})

// jsdom은 scrollIntoView를 구현하지 않음 (MessageList의 자동 스크롤에서 사용)
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = vi.fn()
}

// jsdom에는 Web Audio API가 없음 — AudioQueue/AudioPlayer 테스트용 최소 스텁
class MockAudioBufferSourceNode {
  buffer: unknown = null
  onended: (() => void) | null = null
  connect = vi.fn()
  start = vi.fn()
  stop = vi.fn()
}

class MockAudioContext {
  state = 'running'
  destination = {}
  createBufferSource = vi.fn(() => new MockAudioBufferSourceNode())
  decodeAudioData = vi.fn(() => Promise.resolve({} as AudioBuffer))
  resume = vi.fn(() => Promise.resolve())
  close = vi.fn(() => Promise.resolve())
}

vi.stubGlobal('AudioContext', MockAudioContext)

if (!URL.createObjectURL) {
  URL.createObjectURL = vi.fn(() => 'blob:mock-url')
}
if (!URL.revokeObjectURL) {
  URL.revokeObjectURL = vi.fn()
}

// jsdom의 HTMLMediaElement는 play/pause를 구현하지 않아 경고를 던짐 (AudioPlayer 테스트용)
if (typeof window !== 'undefined') {
  window.HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined)
  window.HTMLMediaElement.prototype.pause = vi.fn()
}
