import { useEffect, useRef } from 'react'
import { useAudioAnalyser } from './useAudioAnalyser'
import { maxAmplitudeDeviation } from '@/lib/audioAnalysis'
import { VOICE_AMPLITUDE_THRESHOLD } from '@/lib/constants'

// 실전 모드에서 "전화 통화처럼" 자연스럽게 턴을 넘기기 위한 무음 지속 시간.
// 1.5초는 너무 짧아서 "Umm..." 같은 필러 뒤에 생각하는 잠깐의 침묵에도 끼어드는
// 느낌이 있었다 — 2.5초로 늘려 자연스럽게 생각할 시간을 좀 더 준다.
const SILENCE_DURATION_MS = 2500

// 실전 모드 전용 — 녹음 중 사용자가 말을 하다가 일정 시간(SILENCE_DURATION_MS) 동안
// 침묵하면 onSilence를 호출해 "답변 완료"를 누른 것처럼 자동으로 턴을 넘긴다.
// 마이크를 켠 직후의 무음(아직 말을 시작 안 한 상태)은 트리거하지 않는다 — 실제로
// 한 번 발화가 감지된 "이후의" 침묵만 턴 종료 신호로 본다.
export function useAutoStopOnSilence(
  stream: MediaStream | null,
  enabled: boolean,
  onSilence: () => void
): void {
  const onSilenceRef = useRef(onSilence)
  onSilenceRef.current = onSilence

  const hasSpokenRef = useRef(false)
  const silenceStartedAtRef = useRef<number | null>(null)
  const firedRef = useRef(false)

  // stream/enabled가 바뀔 때마다(녹음 재시작 등) 판단 상태를 새로 시작한다.
  useEffect(() => {
    hasSpokenRef.current = false
    silenceStartedAtRef.current = null
    firedRef.current = false
  }, [stream, enabled])

  useAudioAnalyser(stream, enabled, (dataArray) => {
    if (firedRef.current) return

    const isSpeaking = maxAmplitudeDeviation(dataArray) > VOICE_AMPLITUDE_THRESHOLD

    if (isSpeaking) {
      hasSpokenRef.current = true
      silenceStartedAtRef.current = null
      return
    }

    if (!hasSpokenRef.current) return // 아직 발화가 감지된 적 없으면(마이크 막 켠 직후 등) 무시

    if (silenceStartedAtRef.current === null) {
      silenceStartedAtRef.current = performance.now()
      return
    }

    if (performance.now() - silenceStartedAtRef.current >= SILENCE_DURATION_MS) {
      firedRef.current = true
      onSilenceRef.current()
    }
  })
}
