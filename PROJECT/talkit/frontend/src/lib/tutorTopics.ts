// AI 튜터(자유대화) 진입 시 사용자가 고르는 주제 목록.
// id는 backend/app/services/ai/chat_service.rb의 TOPICS 키와 1:1로 매칭된다.
// 주제 선택 UI에 노출되는 항목 하나를 표현한다.
export interface TutorTopic {
  id: string
  label: string
}

export const TUTOR_TOPICS: TutorTopic[] = [
  { id: 'tutor_travel', label: '여행' },
  { id: 'tutor_daily_life', label: '일상과 취미' },
  { id: 'tutor_food', label: '음식과 요리' },
  { id: 'tutor_career', label: '직장과 커리어' },
  { id: 'tutor_tech', label: '기술과 트렌드' },
  { id: 'tutor_self_improvement', label: '교육과 자기계발' },
  { id: 'tutor_society', label: '사회와 가치관' },
  { id: 'tutor_sports', label: '운동과 스포츠' },
  { id: 'tutor_music', label: '음악' },
  { id: 'tutor_reading', label: '독서' },
  { id: 'tutor_youtube', label: '유튜브' },
  { id: 'tutor_drama_movie', label: '드라마와 영화' },
  { id: 'tutor_environment', label: '기후, 환경, 자연' },
]
