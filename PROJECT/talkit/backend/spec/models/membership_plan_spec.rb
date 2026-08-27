# MembershipPlan 모델의 검증, 스코프, 기능/만료일 계산 메서드를 검증하는 스펙
require "rails_helper"

RSpec.describe MembershipPlan, type: :model do
  # validate_uniqueness_of 등 shoulda matcher가 비교용 레코드를 만들 때
  # 필수 컬럼이 비어 NOT NULL 제약을 위반하지 않도록 유효한 subject를 지정한다.
  subject { build(:membership_plan) }

  # ─── Associations ────────────────────────────────────────────────────────────
  it { is_expected.to have_many(:user_memberships) }
  it { is_expected.to have_many(:payments) }

  # ─── Validations ─────────────────────────────────────────────────────────────
  it { is_expected.to validate_presence_of(:name) }
  it { is_expected.to validate_uniqueness_of(:name) }
  it { is_expected.to validate_length_of(:name).is_at_most(100) }
  it { is_expected.to validate_presence_of(:duration_days) }
  it { is_expected.to validate_presence_of(:price_cents) }
  it { is_expected.to validate_presence_of(:currency) }

  describe "duration_days numericality" do
    it "정수 양수 값을 허용한다" do
      plan = build(:membership_plan, duration_days: 30)
      expect(plan).to be_valid
    end

    it "0을 거부한다" do
      plan = build(:membership_plan, duration_days: 0)
      expect(plan).not_to be_valid
    end

    it "음수를 거부한다" do
      plan = build(:membership_plan, duration_days: -5)
      expect(plan).not_to be_valid
    end
  end

  describe "price_cents numericality" do
    it "0을 허용한다 (무료 플랜)" do
      plan = build(:membership_plan, price_cents: 0)
      expect(plan).to be_valid
    end

    it "음수를 거부한다" do
      plan = build(:membership_plan, price_cents: -1)
      expect(plan).not_to be_valid
    end
  end

  describe "currency inclusion" do
    it "KRW를 허용한다" do
      plan = build(:membership_plan, currency: "KRW")
      expect(plan).to be_valid
    end

    it "USD를 허용한다" do
      plan = build(:membership_plan, currency: "USD")
      expect(plan).to be_valid
    end

    it "지원하지 않는 통화를 거부한다" do
      plan = build(:membership_plan, currency: "EUR")
      expect(plan).not_to be_valid
    end
  end

  # ─── Custom validation: at_least_one_feature_enabled ─────────────────────────
  describe "#at_least_one_feature_enabled" do
    it "모든 기능이 false이면 유효하지 않다" do
      plan = build(:membership_plan,
                   feature_learning:     false,
                   feature_conversation: false,
                   feature_analysis:     false)
      expect(plan).not_to be_valid
      expect(plan.errors[:base]).to include("최소 하나의 기능 권한을 활성화해야 합니다")
    end

    it "하나의 기능만 활성화되어도 유효하다" do
      plan = build(:membership_plan,
                   feature_learning:     true,
                   feature_conversation: false,
                   feature_analysis:     false)
      expect(plan).to be_valid
    end
  end

  # ─── .active scope ───────────────────────────────────────────────────────────
  describe ".active" do
    let!(:active_plan)   { create(:membership_plan) }
    let!(:inactive_plan) { create(:membership_plan, :inactive) }

    it "active: true인 플랜만 반환한다" do
      expect(MembershipPlan.active).to include(active_plan)
      expect(MembershipPlan.active).not_to include(inactive_plan)
    end
  end

  # ─── #features ───────────────────────────────────────────────────────────────
  describe "#features" do
    it "활성화된 기능 심볼 배열을 반환한다" do
      plan = build(:membership_plan, :premium)
      expect(plan.features).to contain_exactly(:learning, :conversation, :analysis)
    end

    it "베이직 플랜은 learning만 반환한다" do
      plan = build(:membership_plan, :basic)
      expect(plan.features).to contain_exactly(:learning)
    end

    it "conversation만 활성화된 경우 [:conversation]을 반환한다" do
      plan = build(:membership_plan,
                   feature_learning:     false,
                   feature_conversation: true,
                   feature_analysis:     false)
      expect(plan.features).to eq([:conversation])
    end
  end

  # ─── #expires_at_from ────────────────────────────────────────────────────────
  describe "#expires_at_from" do
    let(:plan) { build(:membership_plan, duration_days: 30) }

    it "starts_at + duration_days를 반환한다" do
      starts = Time.zone.parse("2026-01-01 00:00:00")
      expect(plan.expires_at_from(starts)).to eq(starts + 30.days)
    end

    it "60일 플랜에 대해 올바르게 계산한다" do
      plan_60 = build(:membership_plan, :premium, duration_days: 60)
      starts  = Time.zone.parse("2026-06-01 00:00:00")
      expect(plan_60.expires_at_from(starts)).to eq(starts + 60.days)
    end
  end
end
