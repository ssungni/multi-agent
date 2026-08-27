import { describe, it, expect, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AudioPlayer } from './AudioPlayer'

describe('AudioPlayer', () => {
  it('초기 상태는 "다시 듣기" 타이틀을 가진다', () => {
    render(<AudioPlayer audioUrls={['blob:audio-1']} />)
    expect(screen.getByTitle('다시 듣기')).toBeInTheDocument()
  })

  it('클릭하면 재생 상태로 전환되어 "정지" 타이틀을 보인다', async () => {
    render(<AudioPlayer audioUrls={['blob:audio-1']} />)

    await userEvent.click(screen.getByTitle('다시 듣기'))

    expect(screen.getByTitle('정지')).toBeInTheDocument()
  })

  it('재생 중 다시 클릭하면 정지하고 "다시 듣기"로 돌아간다', async () => {
    render(<AudioPlayer audioUrls={['blob:audio-1']} />)

    const button = screen.getByTitle('다시 듣기')
    await userEvent.click(button)
    expect(screen.getByTitle('정지')).toBeInTheDocument()

    await userEvent.click(screen.getByTitle('정지'))
    expect(screen.getByTitle('다시 듣기')).toBeInTheDocument()
  })

  it('클립이 여러 개면 순서대로 이어서 재생하고, 마지막 클립이 끝나면 정지 상태로 돌아간다', async () => {
    const playSpy = vi.spyOn(window.HTMLMediaElement.prototype, 'play')
    render(<AudioPlayer audioUrls={['blob:audio-1', 'blob:audio-2']} />)

    await userEvent.click(screen.getByTitle('다시 듣기'))
    expect(playSpy).toHaveBeenCalledTimes(1)

    // 첫 번째 클립 재생이 끝났다고 시뮬레이션 — 두 번째 클립이 이어서 재생되어야 한다
    const firstAudio = playSpy.mock.contexts[0] as unknown as HTMLAudioElement
    act(() => firstAudio.onended?.(new Event('ended')))
    expect(playSpy).toHaveBeenCalledTimes(2)
    expect(screen.getByTitle('정지')).toBeInTheDocument()

    // 두 번째(마지막) 클립도 끝나면 더 이상 재생할 게 없으므로 "다시 듣기"로 돌아간다
    const secondAudio = playSpy.mock.contexts[1] as unknown as HTMLAudioElement
    act(() => secondAudio.onended?.(new Event('ended')))
    expect(screen.getByTitle('다시 듣기')).toBeInTheDocument()
  })
})
