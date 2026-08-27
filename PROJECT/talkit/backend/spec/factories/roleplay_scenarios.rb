# RoleplayScenario 모델 테스트용 팩토리
FactoryBot.define do
  factory :roleplay_scenario do
    sequence(:series_title) { |n| "시리즈 #{n}" }
    sequence(:title) { |n| "시나리오 #{n}" }
    level { "Basic" }
    description { "시나리오 설명입니다." }
    position { 0 }
    topic_id { "workplace_english" }
  end
end
