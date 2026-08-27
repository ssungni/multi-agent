// 마이크 입력 스트림의 음량 파형을 canvas에 실시간으로 그려주는 훅
import { useEffect } from 'react'
import type { RefObject } from 'react'
import { useAudioAnalyser } from './useAudioAnalyser'

export function useWaveform(canvasRef: RefObject<HTMLCanvasElement>, stream: MediaStream | null) {
  // 스트림이 사라지면(녹음 종료 등) 마지막 프레임이 화면에 멈춰있지 않도록 지운다.
  useEffect(() => {
    if (stream) return
    const canvas = canvasRef.current
    const canvasCtx = canvas?.getContext('2d')
    if (canvas && canvasCtx) canvasCtx.clearRect(0, 0, canvas.width, canvas.height)
  }, [stream, canvasRef])

  useAudioAnalyser(stream, stream !== null, (dataArray) => {
    const canvas = canvasRef.current
    const canvasCtx = canvas?.getContext('2d')
    if (!canvas || !canvasCtx) return

    canvasCtx.clearRect(0, 0, canvas.width, canvas.height)
    canvasCtx.lineWidth = 2
    canvasCtx.strokeStyle = 'hsl(262.1 83.3% 57.8%)'
    canvasCtx.beginPath()

    const sliceWidth = canvas.width / dataArray.length
    let x = 0
    for (let i = 0; i < dataArray.length; i++) {
      const y = (dataArray[i]! / 128) * (canvas.height / 2)
      if (i === 0) canvasCtx.moveTo(x, y)
      else canvasCtx.lineTo(x, y)
      x += sliceWidth
    }
    canvasCtx.lineTo(canvas.width, canvas.height / 2)
    canvasCtx.stroke()
  })
}
