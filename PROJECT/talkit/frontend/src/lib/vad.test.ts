import { describe, it, expect, vi, beforeEach } from 'vitest'
import { trimSilence } from './vad'

// jsdom의 Blob에는 arrayBuffer()가 구현되어 있지 않으므로, encodeWav()가 만든
// 실제 Blob도 읽을 수 있도록 전역에 폴리필을 채워둔다.
if (!Blob.prototype.arrayBuffer) {
  Blob.prototype.arrayBuffer = function (this: Blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as ArrayBuffer)
      reader.onerror = () => reject(reader.error)
      reader.readAsArrayBuffer(this)
    })
  }
}

function makeBlob(): Blob {
  const blob = new Blob(['fake-audio-bytes'])
  if (!blob.arrayBuffer) {
    ;(blob as unknown as { arrayBuffer: () => Promise<ArrayBuffer> }).arrayBuffer = () =>
      Promise.resolve(new ArrayBuffer(8))
  }
  return blob
}

// silence(0) + speech(큰 값) + silence(0)로 이루어진 PCM을 만든다.
function makeAudioBuffer(samples: Float32Array, sampleRate = 16000) {
  return {
    sampleRate,
    getChannelData: (channel: number) => {
      expect(channel).toBe(0)
      return samples
    },
  } as unknown as AudioBuffer
}

function stubAudioContext(decodeImpl: () => Promise<AudioBuffer>) {
  const close = vi.fn(() => Promise.resolve())
  vi.stubGlobal(
    'AudioContext',
    vi.fn(() => ({
      decodeAudioData: vi.fn(decodeImpl),
      close,
    }))
  )
  return { close }
}

describe('trimSilence', () => {
  beforeEach(() => {
    vi.unstubAllGlobals()
  })

  it('전체가 무음이면 hadSpeech: false를 반환하고 원본 blob을 그대로 돌려준다', async () => {
    const silence = new Float32Array(16000 * 2) // 2초 무음
    stubAudioContext(() => Promise.resolve(makeAudioBuffer(silence)))
    const input = makeBlob()

    const result = await trimSilence(input)

    expect(result.hadSpeech).toBe(false)
    expect(result.blob).toBe(input)
  })

  it('앞뒤 무음을 잘라내고 발화 구간(+패딩)만 WAV로 인코딩해 반환한다', async () => {
    const sampleRate = 16000
    const silenceLen = sampleRate // 1초
    const speechLen = sampleRate // 1초
    const total = silenceLen + speechLen + silenceLen
    const samples = new Float32Array(total)
    for (let i = silenceLen; i < silenceLen + speechLen; i++) samples[i] = 0.5 // 발화 구간(큰 값)

    stubAudioContext(() => Promise.resolve(makeAudioBuffer(samples, sampleRate)))

    const result = await trimSilence(makeBlob(), { paddingMs: 100 })

    expect(result.hadSpeech).toBe(true)
    expect(result.blob.type).toBe('audio/wav')

    // WAV 헤더(44바이트) + 16비트 PCM 데이터 길이를 검증한다.
    // 발화 구간(1초) ± 패딩(100ms × 2) ≈ 1.2초 분량이어야 한다 (앞뒤 무음은 대부분 제거됨).
    const buffer = await result.blob.arrayBuffer()
    const dataBytes = buffer.byteLength - 44
    const expectedSamples = speechLen + Math.round((sampleRate * 100) / 1000) * 2
    expect(dataBytes / 2).toBeCloseTo(expectedSamples, -2) // 샘플 수(반올림 오차 허용)

    const view = new DataView(buffer)
    const magic = String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3))
    expect(magic).toBe('RIFF')
  })

  it('디코딩에 실패하면 원본 blob을 그대로 반환한다 (STT 자체는 막지 않음)', async () => {
    stubAudioContext(() => Promise.reject(new Error('decode failed')))
    const input = makeBlob()

    const result = await trimSilence(input)

    expect(result.hadSpeech).toBe(true)
    expect(result.blob).toBe(input)
  })

  it('rmsThreshold를 더 높게 주면 작은 소리는 무음으로 판단한다', async () => {
    const quiet = new Float32Array(16000)
    quiet.fill(0.02, 1000, 2000) // 작은 소리

    stubAudioContext(() => Promise.resolve(makeAudioBuffer(quiet)))

    const result = await trimSilence(makeBlob(), { rmsThreshold: 0.5 })

    expect(result.hadSpeech).toBe(false)
  })
})
