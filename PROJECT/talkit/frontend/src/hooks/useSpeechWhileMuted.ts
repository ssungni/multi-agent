import { useEffect, useState } from 'react'
import { useAudioAnalyser } from './useAudioAnalyser'
import { maxAmplitudeDeviation } from '@/lib/audioAnalysis'
import { VOICE_AMPLITUDE_THRESHOLD } from '@/lib/constants'

// 음소거 중(마이크 스트림은 살아있지만 MediaRecorder는 일시정지된 상태)에 사용자가 말을
// 하고 있는지 감지한다. Waveform과는 별개의 AnalyserNode를 사용해, 화면에 선을 그리지
// 않고도 "음소거인데 소리가 들리는지"만 가볍게 체크한다.
export function useSpeechWhileMuted(stream: MediaStream | null, isMuted: boolean): boolean {
  const [detected, setDetected] = useState(false)
  const enabled = stream !== null && isMuted

  useEffect(() => {
    if (!enabled) setDetected(false)
  }, [enabled])

  useAudioAnalyser(stream, enabled, (dataArray) => {
    setDetected(maxAmplitudeDeviation(dataArray) > VOICE_AMPLITUDE_THRESHOLD)
  })

  return detected
}
