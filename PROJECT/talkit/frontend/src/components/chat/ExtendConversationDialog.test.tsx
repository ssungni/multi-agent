import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ExtendConversationDialog } from './ExtendConversationDialog'

describe('ExtendConversationDialog', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('open이 false이면 내용이 보이지 않는다', () => {
    render(
      <ExtendConversationDialog open={false} onExtend={vi.fn()} onEnd={vi.fn()} onTimeout={vi.fn()} />
    )
    expect(screen.queryByText('대화를 연장하시겠습니까?')).not.toBeInTheDocument()
  })

  it('open이 true이면 연장 안내 문구(30분 한도 포함)를 표시한다', () => {
    render(<ExtendConversationDialog open onExtend={vi.fn()} onEnd={vi.fn()} onTimeout={vi.fn()} />)
    expect(screen.getByText('대화를 연장하시겠습니까?')).toBeInTheDocument()
    expect(screen.getByText(/대화를 시작한 지 5분이 지났어요/)).toBeInTheDocument()
    expect(screen.getByText(/최대 30분까지 연장할 수 있어요/)).toBeInTheDocument()
  })

  it('연장하기 클릭 시 onExtend가 호출된다', async () => {
    vi.useRealTimers()
    const onExtend = vi.fn()
    render(
      <ExtendConversationDialog open onExtend={onExtend} onEnd={vi.fn()} onTimeout={vi.fn()} />
    )

    await userEvent.click(screen.getByRole('button', { name: '연장하기' }))

    expect(onExtend).toHaveBeenCalledTimes(1)
  })

  it('종료하기 클릭 시 onEnd가 호출된다', async () => {
    vi.useRealTimers()
    const onEnd = vi.fn()
    render(<ExtendConversationDialog open onExtend={vi.fn()} onEnd={onEnd} onTimeout={vi.fn()} />)

    await userEvent.click(screen.getByRole('button', { name: '종료하기' }))

    expect(onEnd).toHaveBeenCalledTimes(1)
  })

  it('30초 동안 아무 응답이 없으면 onTimeout이 호출된다', () => {
    const onTimeout = vi.fn()
    render(<ExtendConversationDialog open onExtend={vi.fn()} onEnd={vi.fn()} onTimeout={onTimeout} />)

    expect(onTimeout).not.toHaveBeenCalled()

    act(() => {
      vi.advanceTimersByTime(30 * 1000)
    })

    expect(onTimeout).toHaveBeenCalledTimes(1)
  })

  it('30초가 되기 전에 닫히면(open=false) onTimeout이 호출되지 않는다', () => {
    const onTimeout = vi.fn()
    const { rerender } = render(
      <ExtendConversationDialog open onExtend={vi.fn()} onEnd={vi.fn()} onTimeout={onTimeout} />
    )

    act(() => {
      vi.advanceTimersByTime(10 * 1000)
    })
    rerender(
      <ExtendConversationDialog
        open={false}
        onExtend={vi.fn()}
        onEnd={vi.fn()}
        onTimeout={onTimeout}
      />
    )

    act(() => {
      vi.advanceTimersByTime(30 * 1000)
    })

    expect(onTimeout).not.toHaveBeenCalled()
  })
})
