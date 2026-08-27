# Payment 모델 테스트용 팩토리 (completed/failed 트레이트로 PG 응답 시뮬레이션)
FactoryBot.define do
  factory :payment do
    association :user
    association :membership_plan
    amount_cents { membership_plan.price_cents }
    currency     { "KRW" }
    status       { :pending }

    trait :completed do
      status { :completed }

      after(:build) do |payment|
        txn_id = "mock_#{SecureRandom.hex(8)}"
        payment.pg_transaction_id = txn_id
        payment.pg_response = { "success" => true, "transaction_id" => txn_id }
      end
    end

    trait :failed do
      status      { :failed }
      pg_response { { "success" => false, "error" => "insufficient_funds" } }
    end
  end
end
