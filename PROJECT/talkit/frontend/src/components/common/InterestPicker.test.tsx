import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { InterestPicker } from './InterestPicker'
import { TUTOR_TOPICS } from '@/lib/tutorTopics'

describe('InterestPicker', () => {
  it('TUTOR_TOPICS의 모든 주제를 버튼으로 표시한다', () => {
    render(<InterestPicker selected={[]} onToggle={vi.fn()} />)

    for (const topic of TUTOR_TOPICS) {
      expect(screen.getByRole('button', { name: new RegExp(topic.label) })).toBeInTheDocument()
    }
  })

  it('selected에 포함된 주제는 aria-pressed=true이고 체크 아이콘이 보인다', () => {
    render(<InterestPicker selected={['tutor_food']} onToggle={vi.fn()} />)

    const foodButton = screen.getByRole('button', { name: /음식과 요리/ })
    expect(foodButton).toHaveAttribute('aria-pressed', 'true')
  })

  it('선택되지 않은 주제는 aria-pressed=false이다', () => {
    render(<InterestPicker selected={['tutor_food']} onToggle={vi.fn()} />)

    const travelButton = screen.getByRole('button', { name: /여행/ })
    expect(travelButton).toHaveAttribute('aria-pressed', 'false')
  })

  it('버튼을 클릭하면 onToggle이 해당 topicId와 함께 호출된다', async () => {
    const onToggle = vi.fn()
    render(<InterestPicker selected={[]} onToggle={onToggle} />)

    await userEvent.click(screen.getByRole('button', { name: /음악/ }))

    expect(onToggle).toHaveBeenCalledWith('tutor_music')
  })
})
