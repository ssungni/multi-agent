// AudioContext + AnalyserNode 생명주기를 관리하는 저수준 공유 훅.
// 파형 그리기(useWaveform) / 침묵 감지(useAutoStopOnSilence) / 음소거 중 발화 감지
// (useSpeechWhileMuted)가 각자 AudioContext 생성·연결·해제를 반복 구현하던 것을 통합한다.
// onFrame은 매 애니메이션 프레임마다 그 시점의 시간 도메인 데이터를 받는다.
import { useEffect, useRef } from 'react'

export function useAudioAnalyser(
  stream: MediaStream | null,
  enabled: boolean,
  onFrame: (dataArray: Uint8Array) => void
): void {
  const rafRef = useRef(0)
  const onFrameRef = useRef(onFrame)
  onFrameRef.current = onFrame

  useEffect(() => {
    if (!stream || !enabled) return

    const ctx = new AudioContext()
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 256
    const source = ctx.createMediaStreamSource(stream)
    source.connect(analyser)
    const dataArray = new Uint8Array(analyser.frequencyBinCount)

    const tick = () => {
      rafRef.current = requestAnimationFrame(tick)
      analyser.getByteTimeDomainData(dataArray)
      onFrameRef.current(dataArray)
    }
    tick()

    return () => {
      cancelAnimationFrame(rafRef.current)
      source.disconnect()
      void ctx.close()
    }
  }, [stream, enabled])
}
