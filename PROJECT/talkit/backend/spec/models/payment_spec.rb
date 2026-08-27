# Payment 모델의 검증, enum 상태, 가격 일치 검증을 검증하는 스펙
require "rails_helper"

RSpec.describe Payment, type: :model do
  # ─── Associations ────────────────────────────────────────────────────────────
  it { is_expected.to belong_to(:user) }
  it { is_expected.to belong_to(:membership_plan) }
  it { is_expected.to have_one(:user_membership) }

  # ─── Enum ────────────────────────────────────────────────────────────────────
  it do
    is_expected.to define_enum_for(:status)
      .with_values(pending: "pending", completed: "completed", failed: "failed")
      .backed_by_column_of_type(:string)
  end

  # ─── Validations ─────────────────────────────────────────────────────────────
  it { is_expected.to validate_presence_of(:amount_cents) }
  it { is_expected.to validate_presence_of(:currency) }

  describe "amount_cents numericality" do
    it "양수를 허용한다 (플랜 가격과 일치하는 경우)" do
      # amount_matches_plan_price 검증과 충돌하지 않도록 플랜 가격에 맞춰 생성한다.
      plan    = create(:membership_plan, price_cents: 1000)
      payment = build(:payment, membership_plan: plan, amount_cents: 1000)
      expect(payment).to be_valid
    end

    it "0을 거부한다" do
      payment = build(:payment, amount_cents: 0)
      expect(payment).not_to be_valid
    end

    it "음수를 거부한다" do
      payment = build(:payment, amount_cents: -100)
      expect(payment).not_to be_valid
    end
  end

  describe "currency inclusion" do
    it "KRW를 허용한다" do
      payment = build(:payment, currency: "KRW")
      expect(payment).to be_valid
    end

    it "지원하지 않는 통화를 거부한다" do
      payment = build(:payment, currency: "EUR")
      expect(payment).not_to be_valid
    end
  end

  describe "pg_transaction_id uniqueness" do
    let(:user) { create(:user) }
    let(:plan) { create(:membership_plan, :premium) }

    it "동일한 pg_transaction_id를 가진 두 번째 결제를 거부한다" do
      create(:payment, user: user, membership_plan: plan,
             status: :completed, pg_transaction_id: "txn_abc")
      duplicate = build(:payment, user: user, membership_plan: plan,
                         status: :completed, pg_transaction_id: "txn_abc")
      expect(duplicate).not_to be_valid
      expect(duplicate.errors[:pg_transaction_id]).to be_present
    end

    it "nil pg_transaction_id는 중복 허용된다" do
      create(:payment, user: user, membership_plan: plan, pg_transaction_id: nil)
      second = build(:payment, user: user, membership_plan: plan, pg_transaction_id: nil)
      expect(second).to be_valid
    end
  end

  # ─── Custom validation: amount_matches_plan_price (on: :create) ───────────────
  describe "#amount_matches_plan_price" do
    let(:user) { create(:user) }
    let(:plan) { create(:membership_plan, :premium, price_cents: 219_000) }

    context "amount_cents가 플랜 가격과 일치하는 경우" do
      it "유효하다" do
        payment = build(:payment, user: user, membership_plan: plan, amount_cents: 219_000)
        expect(payment).to be_valid
      end
    end

    context "amount_cents가 플랜 가격과 다른 경우" do
      it "유효하지 않다" do
        payment = build(:payment, user: user, membership_plan: plan, amount_cents: 100_000)
        expect(payment).not_to be_valid
        expect(payment.errors[:amount_cents]).to include(/플랜 가격/)
      end
    end

    context "update 시에는 가격 검증을 건너뛴다" do
      let!(:payment) { create(:payment, :completed, user: user, membership_plan: plan) }

      it "업데이트 후 amount_cents 변경이 허용된다" do
        # on: :create 이므로 update에서는 검증 안함
        payment.update_column(:amount_cents, 999)
        payment.reload
        expect(payment.amount_cents).to eq(999)
      end
    end
  end

  # ─── Status transitions ───────────────────────────────────────────────────────
  describe "status transitions" do
    let(:payment) { create(:payment) }

    it "pending → completed 가능" do
      payment.update!(status: :completed)
      expect(payment.reload.status).to eq("completed")
    end

    it "pending → failed 가능" do
      payment.update!(status: :failed)
      expect(payment.reload.status).to eq("failed")
    end

    it "factory :completed 트레이트가 올바르게 동작한다" do
      p = create(:payment, :completed, user: create(:user), membership_plan: create(:membership_plan, :premium))
      expect(p.status).to eq("completed")
      expect(p.pg_transaction_id).to be_present
    end
  end
end
