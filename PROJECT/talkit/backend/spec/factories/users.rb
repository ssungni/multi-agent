# User 모델 테스트용 팩토리
FactoryBot.define do
  factory :user do
    sequence(:email) { |n| "user#{n}@example.com" }
    name { Faker::Name.name }
    phone_number { Faker::PhoneNumber.cell_phone }
    password { "password123" }
  end
end
