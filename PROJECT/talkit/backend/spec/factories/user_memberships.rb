# UserMembership 모델 테스트용 팩토리 (활성/만료/삭제/결제부여 등 다양한 상태 트레이트 제공)
FactoryBot.define do
  factory :user_membership do
    association :user
    association :membership_plan
    granted_by { :admin }   # admin은 payment 불필요 → 기본 트레이트에서 validation 통과
    starts_at  { 1.day.ago }
    expires_at { 29.days.from_now }
    deleted_at { nil }

    # 결제로 부여된 멤버십 (payment 연결 필요)
    trait :payment_granted do
      granted_by { :payment }

      after(:build) do |membership|
        membership.payment ||= build(:payment, :completed,
          user:            membership.user,
          membership_plan: membership.membership_plan)
      end
    end

    trait :active do
      starts_at  { 1.day.ago }
      expires_at { 30.days.from_now }
      deleted_at { nil }
    end

    trait :expired do
      starts_at  { 61.days.ago }
      expires_at { 1.day.ago }
      deleted_at { nil }
    end

    trait :deleted do
      deleted_at { 1.hour.ago }
    end

    trait :premium do
      association :membership_plan, factory: [:membership_plan, :premium]
    end
  end
end
