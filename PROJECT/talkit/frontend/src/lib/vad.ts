// 마이크로 녹음한 오디오에서 VAD(음성 활동 감지, Voice Activity Detection)로 앞뒤
// 무음 구간을 잘라내고, 실제로 말한 부분만 WAV로 다시 인코딩해 STT로 보낸다.
// (Whisper가 무음에서 환각 텍스트를 만드는 것을 입력 단계에서부터 줄이고,
// 불필요한 무음을 보내지 않아 업로드 용량/지연도 줄어든다.)

const FRAME_DURATION_MS = 20
// useAudioRecorder가 autoGainControl을 켜둬서 마이크 입력 레벨이 어느 정도
// 정규화되어 있으므로, 절대 RMS 임계값으로도 충분히 안정적으로 동작한다.
const DEFAULT_RMS_THRESHOLD = 0.01
// 단어의 시작/끝이 잘리지 않도록 감지된 발화 구간 앞뒤에 여유를 둔다.
const DEFAULT_PADDING_MS = 200

export interface TrimSilenceResult {
  blob: Blob
  // false면 클립 전체가 무음으로 판단되었다는 뜻 — 호출 측에서 STT 요청 자체를 건너뛸 수 있다.
  hadSpeech: boolean
}

export interface TrimSilenceOptions {
  rmsThreshold?: number
  paddingMs?: number
}

// 오디오 blob을 프레임 단위로 분석해 무음 구간을 잘라내고, 발화 구간만 WAV로 재인코딩한다.
export async function trimSilence(
  input: Blob,
  opts: TrimSilenceOptions = {}
): Promise<TrimSilenceResult> {
  const rmsThreshold = opts.rmsThreshold ?? DEFAULT_RMS_THRESHOLD
  const paddingMs = opts.paddingMs ?? DEFAULT_PADDING_MS

  const ctx = new AudioContext()
  let audioBuffer: AudioBuffer
  try {
    const arrayBuffer = await input.arrayBuffer()
    audioBuffer = await ctx.decodeAudioData(arrayBuffer)
  } catch {
    // 디코딩 실패 시 원본을 그대로 보낸다 — 무음 제거는 최적화일 뿐,
    // 이것 때문에 STT 자체가 막혀서는 안 된다.
    void ctx.close()
    return { blob: input, hadSpeech: true }
  }

  const sampleRate = audioBuffer.sampleRate
  const samples = audioBuffer.getChannelData(0) // 마이크는 1채널로 녹음하므로 채널 0만 본다
  const frameSize = Math.max(1, Math.round((sampleRate * FRAME_DURATION_MS) / 1000))
  const frameCount = Math.ceil(samples.length / frameSize)

  let firstSpeechFrame = -1
  let lastSpeechFrame = -1

  // FRAME_DURATION_MS 단위로 잘라 각 프레임의 RMS(에너지)를 구하고, 임계값을 넘는
  // 첫/마지막 프레임을 찾아 실제 발화 구간의 경계로 사용한다.
  for (let f = 0; f < frameCount; f++) {
    const start = f * frameSize
    const end = Math.min(start + frameSize, samples.length)
    let sumSquares = 0
    for (let i = start; i < end; i++) sumSquares += samples[i]! * samples[i]!
    const rms = Math.sqrt(sumSquares / (end - start))

    if (rms >= rmsThreshold) {
      if (firstSpeechFrame === -1) firstSpeechFrame = f
      lastSpeechFrame = f
    }
  }

  void ctx.close()

  // 임계값을 넘는 프레임이 하나도 없으면 클립 전체가 무음이라는 뜻이다.
  if (firstSpeechFrame === -1) {
    return { blob: input, hadSpeech: false }
  }

  // 발화 구간 경계에 패딩을 더해 자연스러운 시작/끝을 보존하되, 배열 범위를 벗어나지 않게 한다.
  const paddingSamples = Math.round((sampleRate * paddingMs) / 1000)
  const startSample = Math.max(0, firstSpeechFrame * frameSize - paddingSamples)
  const endSample = Math.min(samples.length, (lastSpeechFrame + 1) * frameSize + paddingSamples)

  const trimmed = samples.subarray(startSample, endSample)
  return { blob: encodeWav(trimmed, sampleRate), hadSpeech: true }
}

// 16-bit PCM mono WAV로 인코딩한다 (헤더 44바이트 + 샘플 데이터).
function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const bytesPerSample = 2
  const byteRate = sampleRate * bytesPerSample
  const dataSize = samples.length * bytesPerSample

  const buffer = new ArrayBuffer(44 + dataSize)
  const view = new DataView(buffer)

  // 표준 WAV(RIFF) 헤더를 little-endian으로 채운다.
  writeString(view, 0, 'RIFF')
  view.setUint32(4, 36 + dataSize, true)
  writeString(view, 8, 'WAVE')
  writeString(view, 12, 'fmt ')
  view.setUint32(16, 16, true) // fmt chunk size
  view.setUint16(20, 1, true) // PCM
  view.setUint16(22, 1, true) // mono
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, byteRate, true)
  view.setUint16(32, bytesPerSample, true) // block align
  view.setUint16(34, 16, true) // bits per sample
  writeString(view, 36, 'data')
  view.setUint32(40, dataSize, true)

  // Float32(-1~1) 샘플을 16-bit PCM 정수로 변환해 기록한다.
  let offset = 44
  for (let i = 0; i < samples.length; i++) {
    const clamped = Math.max(-1, Math.min(1, samples[i]!))
    view.setInt16(offset, Math.round(clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff), true)
    offset += 2
  }

  return new Blob([buffer], { type: 'audio/wav' })
}

// WAV 헤더에 들어가는 ASCII 문자열(RIFF, WAVE 등)을 DataView에 1바이트씩 기록한다.
function writeString(view: DataView, offset: number, str: string): void {
  for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i))
}
