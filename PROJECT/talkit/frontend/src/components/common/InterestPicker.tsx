// 관심 토픽을 다중 선택할 수 있는 버튼 그리드 컴포넌트 (선택 상태는 부모가 관리하는 controlled 컴포넌트)
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { TUTOR_TOPICS } from '@/lib/tutorTopics'

interface InterestPickerProps {
  selected: string[]
  onToggle: (topicId: string) => void
}

export function InterestPicker({ selected, onToggle }: InterestPickerProps) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {TUTOR_TOPICS.map((topic) => {
        // 현재 토픽이 선택된 목록에 포함되어 있는지로 선택 상태 판단
        const isSelected = selected.includes(topic.id)
        return (
          <button
            key={topic.id}
            type="button"
            aria-pressed={isSelected}
            onClick={() => onToggle(topic.id)}
            className={cn(
              'flex items-center justify-between gap-2 rounded-lg border p-4 text-left text-sm font-medium transition-colors',
              // 선택 여부에 따라 강조 스타일을 다르게 적용
              isSelected
                ? 'border-primary bg-primary/5 text-primary'
                : 'hover:border-primary hover:bg-primary/5'
            )}
          >
            {topic.label}
            {/* 선택된 토픽에만 체크 아이콘을 표시 */}
            {isSelected && <Check className="h-4 w-4 shrink-0" />}
          </button>
        )
      })}
    </div>
  )
}
