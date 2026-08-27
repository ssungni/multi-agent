import { useState, useRef, useCallback } from 'react'
import { Play, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface AudioPlayerProps {
  // 한 메시지가 문장별로 여러 오디오 클립을 가질 수 있다 — 순서대로 이어서 재생한다.
  audioUrls: string[]
  className?: string
}

// 여러 개의 오디오 클립을 순차적으로 이어 재생/정지할 수 있는 재생 버튼
export function AudioPlayer({ audioUrls, className }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // index부터 시작해 순서대로 오디오를 재생하고, 끝나거나 에러가 나면 다음 클립으로 자동 진행한다
  const playFrom = useCallback(
    (index: number) => {
      if (index >= audioUrls.length) {
        setIsPlaying(false)
        return
      }
      const audio = new Audio(audioUrls[index])
      audioRef.current = audio
      audio.onended = () => playFrom(index + 1)
      audio.onerror = () => playFrom(index + 1)
      void audio.play()
    },
    [audioUrls]
  )

  // 재생 중이면 정지하고 위치를 처음으로 되돌리고, 아니면 첫 클립부터 재생을 시작한다
  const toggle = useCallback(() => {
    if (isPlaying) {
      audioRef.current?.pause()
      if (audioRef.current) audioRef.current.currentTime = 0
      setIsPlaying(false)
    } else {
      setIsPlaying(true)
      playFrom(0)
    }
  }, [isPlaying, playFrom])

  return (
    <Button
      variant="ghost"
      size="sm"
      className={cn('h-6 w-6 p-0 opacity-60 hover:opacity-100', className)}
      onClick={toggle}
      title={isPlaying ? '정지' : '다시 듣기'}
    >
      {isPlaying ? <Square className="h-3 w-3" /> : <Play className="h-3 w-3" />}
    </Button>
  )
}
