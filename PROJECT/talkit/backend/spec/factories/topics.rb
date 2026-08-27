# Topic 모델 테스트용 팩토리
FactoryBot.define do
  factory :topic do
    sequence(:title) { |n| "Topic Title #{n}" }
    category  { "테스트 카테고리" }
    image_url { "/images/topics/test.jpeg" }
    english_1 { "English paragraph one." }
    korean_1  { "한국어 문단 1입니다." }
    english_2 { "English paragraph two." }
    korean_2  { "한국어 문단 2입니다." }
    position  { 0 }
  end
end
