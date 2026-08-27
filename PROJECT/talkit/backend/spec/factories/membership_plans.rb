# MembershipPlan 모델 테스트용 팩토리 (basic/premium/inactive 트레이트 제공)
FactoryBot.define do
  factory :membership_plan do
    sequence(:name) { |n| "Plan #{n}" }
    feature_learning     { true }
    feature_conversation { false }
    feature_analysis     { false }
    duration_days { 30 }
    price_cents   { 129_000 }
    currency      { "KRW" }
    active        { true }

    trait :basic do
      name                 { "베이직" }
      feature_learning     { true }
      feature_conversation { false }
      feature_analysis     { false }
      duration_days        { 30 }
      price_cents          { 129_000 }
    end

    trait :premium do
      name                 { "프리미엄" }
      feature_learning     { true }
      feature_conversation { true }
      feature_analysis     { true }
      duration_days        { 60 }
      price_cents          { 219_000 }
    end

    trait :inactive do
      active { false }
    end
  end
end
