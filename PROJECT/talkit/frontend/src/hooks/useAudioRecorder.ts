// 마이크 오디오를 녹음/일시정지/정지하는 MediaRecorder 래퍼 훅
import { useRef, useCallback, useState } from 'react'

export function useAudioRecorder() {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<BlobPart[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const [isRecording, setIsRecording] = useState(false)

  // 마이크 권한을 요청하고 녹음을 시작, 사용된 미디어 스트림을 반환
  const start = useCallback(async (): Promise<MediaStream> => {
    const mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: { ideal: 16000 },
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    })

    streamRef.current = mediaStream
    chunksRef.current = []

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm'
    const recorder = new MediaRecorder(mediaStream, { mimeType })
    mediaRecorderRef.current = recorder

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data)
    }

    recorder.start(100)
    setIsRecording(true)
    return mediaStream
  }, [])

  // 녹음을 종료하고 지금까지 모은 청크를 하나의 Blob으로 합쳐 반환, 마이크 트랙도 해제
  const stop = useCallback(
    (): Promise<Blob> =>
      new Promise((resolve) => {
        const recorder = mediaRecorderRef.current
        if (!recorder || recorder.state === 'inactive') {
          resolve(new Blob([], { type: 'audio/webm' }))
          return
        }
        recorder.onstop = () => {
          const blob = new Blob(chunksRef.current, { type: recorder.mimeType })
          streamRef.current?.getTracks().forEach((t) => t.stop())
          streamRef.current = null
          setIsRecording(false)
          resolve(blob)
        }
        recorder.stop()
      }),
    []
  )

  // 음소거 — MediaRecorder만 일시정지해 그 구간의 오디오가 최종 blob에 섞이지 않게 한다.
  // 마이크 스트림 자체(트랙)는 계속 열려있어서, 음소거 중에도 음량 감지(파장/안내 메시지)는 가능하다.
  const pause = useCallback(() => {
    const recorder = mediaRecorderRef.current
    if (recorder && recorder.state === 'recording') recorder.pause()
  }, [])

  // 음소거 해제 — 일시정지된 녹음을 다시 이어서 진행
  const resume = useCallback(() => {
    const recorder = mediaRecorderRef.current
    if (recorder && recorder.state === 'paused') recorder.resume()
  }, [])

  return { isRecording, start, stop, pause, resume }
}
