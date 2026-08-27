import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AudioRecorder } from './AudioRecorder'

function renderRecorder(
  overrides: Partial<{
    status: 'idle' | 'recording' | 'vad_processing' | 'stt_processing' | 'llm_streaming' | 'tts_playing' | 'ai_opening' | 'error'
    isMuted: boolean
    onStartRecording: () => void
    onToggleMute: () => void
    onSubmit: () => void
  }> = {}
) {
  const props = {
    status: 'idle' as const,
    isMuted: false,
    onStartRecording: vi.fn(),
    onToggleMute: vi.fn(),
    onSubmit: vi.fn(),
    ...overrides,
  }
  const view = render(<AudioRecorder {...props} />)
  return { ...view, props }
}

describe('AudioRecorder', () => {
  it('idle 상태에서는 마이크 버튼만 표시되고 활성화되어 있다', () => {
    renderRecorder({ status: 'idle' })

    const micButton = screen.getByRole('button', { name: '녹음 시작' })
    expect(micButton).toBeEnabled()
    expect(screen.queryByText('답변 완료')).not.toBeInTheDocument()
  })

  it('마이크 버튼 클릭 시 idle에서는 onStartRecording이 호출된다', async () => {
    const onStartRecording = vi.fn()
    renderRecorder({ status: 'idle', onStartRecording })

    await userEvent.click(screen.getByRole('button', { name: '녹음 시작' }))

    expect(onStartRecording).toHaveBeenCalledTimes(1)
  })

  it('recording 상태(음소거 아님)에서는 음소거 버튼과 답변 완료 버튼이 함께 표시된다', () => {
    renderRecorder({ status: 'recording', isMuted: false })

    expect(screen.getByRole('button', { name: '음소거' })).toBeInTheDocument()
    expect(screen.getByText('답변 완료')).toBeInTheDocument()
  })

  it('recording 상태에서 마이크 버튼을 누르면 onToggleMute가 호출된다 (STT를 호출하지 않음)', async () => {
    const onToggleMute = vi.fn()
    const onSubmit = vi.fn()
    renderRecorder({ status: 'recording', isMuted: false, onToggleMute, onSubmit })

    await userEvent.click(screen.getByRole('button', { name: '음소거' }))

    expect(onToggleMute).toHaveBeenCalledTimes(1)
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('답변 완료 버튼을 눌러야 onSubmit이 호출된다', async () => {
    const onSubmit = vi.fn()
    renderRecorder({ status: 'recording', isMuted: false, onSubmit })

    await userEvent.click(screen.getByText('답변 완료'))

    expect(onSubmit).toHaveBeenCalledTimes(1)
  })

  it('음소거 중에는 답변 완료 버튼이 보이지 않는다', () => {
    renderRecorder({ status: 'recording', isMuted: true })

    expect(screen.queryByText('답변 완료')).not.toBeInTheDocument()
  })

  it('음소거 중에 마이크 버튼을 누르면 onToggleMute가 호출되어 다시 켤 수 있다', async () => {
    const onToggleMute = vi.fn()
    renderRecorder({ status: 'recording', isMuted: true, onToggleMute })

    const micButton = screen.getByRole('button', { name: '마이크 켜기' })
    expect(micButton).toBeEnabled()
    await userEvent.click(micButton)

    expect(onToggleMute).toHaveBeenCalledTimes(1)
  })

  it.each(['stt_processing', 'llm_streaming', 'tts_playing', 'ai_opening', 'vad_processing'] as const)(
    '%s 상태에서는 마이크 버튼이 비활성화된다',
    (status) => {
      renderRecorder({ status })
      expect(screen.getByRole('button', { name: '녹음 시작' })).toBeDisabled()
    }
  )

  it('error 상태에서는 마이크 버튼이 다시 활성화된다 (재시도 가능)', () => {
    renderRecorder({ status: 'error' })
    expect(screen.getByRole('button', { name: '녹음 시작' })).toBeEnabled()
  })

  it('recording(음소거 아님) 상태에서는 버튼이 커지고 진한 보라색 + ring으로 강조된다', () => {
    renderRecorder({ status: 'recording', isMuted: false })
    const micButton = screen.getByRole('button', { name: '음소거' })
    expect(micButton.className).toContain('scale-110')
    expect(micButton.className).toContain('bg-green-600')
    expect(micButton.className).toContain('ring-green-400/40')
  })

  it('recording(음소거 아님) 상태에서는 일반 마이크(O) 아이콘이 펄스 애니메이션과 함께 보인다', () => {
    const { container } = renderRecorder({ status: 'recording', isMuted: false })
    expect(container.querySelector('.lucide-mic.animate-pulse')).not.toBeNull()
    expect(container.querySelector('.lucide-mic-off')).toBeNull()
  })

  it('idle(시작 전) 상태에서는 확대/강조 효과 없이 옅은 보라색이고, 슬래시 마이크(∅) 아이콘이 보인다', () => {
    const { container } = renderRecorder({ status: 'idle' })
    const micButton = screen.getByRole('button', { name: '녹음 시작' })
    expect(micButton.className).not.toContain('scale-110')
    expect(micButton.className).toContain('bg-green-300')
    expect(container.querySelector('.lucide-mic-off')).not.toBeNull()
  })

  it('음소거 상태에서도 idle과 동일하게 확대/강조 없이 슬래시 마이크(∅) 아이콘이 보인다', () => {
    const { container } = renderRecorder({ status: 'recording', isMuted: true })
    const micButton = screen.getByRole('button', { name: '마이크 켜기' })
    expect(micButton.className).not.toContain('scale-110')
    expect(micButton.className).toContain('bg-green-300')
    expect(container.querySelector('.lucide-mic-off')).not.toBeNull()
  })
})
