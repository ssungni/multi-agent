import { useRef } from 'react'
import { useWaveform } from '@/hooks/useWaveform'
import { cn } from '@/lib/utils'

interface WaveformProps {
  stream: MediaStream | null
  className?: string
}

// 마이크 입력 스트림을 받아 캔버스에 실시간 파형(음성 시각화)을 그려주는 컴포넌트
export function Waveform({ stream, className }: WaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  // 실제 파형 그리기 로직은 훅에 위임하고, 이 컴포넌트는 캔버스 엘리먼트만 제공
  useWaveform(canvasRef, stream)

  return (
    <canvas
      ref={canvasRef}
      width={320}
      height={64}
      className={cn('w-full rounded-lg bg-muted', className)}
    />
  )
}
