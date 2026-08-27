# UserMembership 모델의 검증, 스코프, 활성/만료 상태 관련 메서드를 검증하는 스펙
require "rails_helper"

RSpec.describe UserMembership, type: :model do
  # ─────────────────────────────────────────────
  # Associations
  # ─────────────────────────────────────────────
  it { is_expected.to belong_to(:user) }
  it { is_expected.to belong_to(:membership_plan) }
  it { is_expected.to belong_to(:payment).optional }

  # ─────────────────────────────────────────────
  # Enum
  # ─────────────────────────────────────────────
  it do
    is_expected.to define_enum_for(:granted_by)
      .with_values(admin: "admin", payment: "payment")
      .backed_by_column_of_type(:string)
  end

  # ─────────────────────────────────────────────
  # Presence validations
  # ─────────────────────────────────────────────
  it { is_expected.to validate_presence_of(:starts_at) }
  it { is_expected.to validate_presence_of(:expires_at) }
  it { is_expected.to validate_presence_of(:granted_by) }

  # ─────────────────────────────────────────────
  # Custom validations
  # ─────────────────────────────────────────────
  describe "#expires_at_after_starts_at" do
    subject(:membership) { build(:user_membership) }

    context "expires_at이 starts_at보다 이전인 경우" do
      before { membership.expires_at = membership.starts_at - 1.day }

      it "유효하지 않다" do
        expect(membership).not_to be_valid
      end

      it "expires_at에 에러를 추가한다" do
        membership.valid?
        expect(membership.errors[:expires_at]).to include("starts_at보다 이후여야 합니다")
      end
    end

    context "expires_at이 starts_at과 같은 경우" do
      before do
        t = Time.current
        membership.starts_at = t
        membership.expires_at = t
      end

      it "유효하지 않다" do
        expect(membership).not_to be_valid
      end
    end

    context "expires_at이 starts_at보다 이후인 경우" do
      it "유효하다" do
        expect(membership).to be_valid
      end
    end
  end

  describe "#payment_required_when_granted_by_payment" do
    let(:user)    { create(:user) }
    let(:plan)    { create(:membership_plan, :premium) }
    let(:payment) { build(:payment, :completed, user: user, membership_plan: plan) }

    context "granted_by가 payment이고 payment가 nil인 경우" do
      subject(:membership) do
        build(:user_membership, user: user, membership_plan: plan,
              granted_by: :payment, payment: nil)
      end

      it "유효하지 않다" do
        expect(membership).not_to be_valid
      end

      it "payment에 에러를 추가한다" do
        membership.valid?
        expect(membership.errors[:payment]).to include("결제 정보가 필요합니다")
      end
    end

    context "granted_by가 payment이고 payment가 존재하는 경우" do
      subject(:membership) do
        build(:user_membership, user: user, membership_plan: plan,
              granted_by: :payment, payment: payment)
      end

      it "유효하다" do
        expect(membership).to be_valid
      end
    end

    context "granted_by가 admin인 경우" do
      subject(:membership) do
        build(:user_membership, user: user, membership_plan: plan,
              granted_by: :admin, payment: nil)
      end

      it "payment 없이도 유효하다" do
        expect(membership).to be_valid
      end
    end
  end

  describe "#no_duplicate_active_membership (on: :create)" do
    let(:user) { create(:user) }
    let(:plan) { create(:membership_plan) }

    subject(:new_membership) { build(:user_membership, user: user, membership_plan: plan) }

    context "유저에게 이미 활성 멤버십이 있는 경우" do
      before { create(:user_membership, :active, user: user) }

      it "유효하지 않다" do
        expect(new_membership).not_to be_valid
      end

      it "user에 에러를 추가한다" do
        new_membership.valid?
        expect(new_membership.errors[:user]).to include("이미 활성 멤버십이 존재합니다")
      end
    end

    context "유저에게 만료된 멤버십만 있는 경우" do
      before { create(:user_membership, :expired, user: user) }

      it "유효하다" do
        expect(new_membership).to be_valid
      end
    end

    context "유저에게 soft-deleted 멤버십만 있는 경우" do
      before { create(:user_membership, :deleted, user: user) }

      it "유효하다" do
        expect(new_membership).to be_valid
      end
    end

    context "다른 유저에게 활성 멤버십이 있는 경우" do
      before { create(:user_membership, :active) }

      it "유효하다 (유저별로 독립적)" do
        expect(new_membership).to be_valid
      end
    end

    context "update 시에는 중복 검사를 건너뛴다" do
      let!(:existing_1) { create(:user_membership, :active, user: user) }

      it "save! 후 expires_at 업데이트가 유효하다" do
        # 두 번째 멤버십을 validation 없이 강제 저장해 데이터 불일치 상황 시뮬레이션
        new_membership.save!(validate: false)
        new_membership.expires_at = 60.days.from_now
        expect(new_membership).to be_valid  # on: :create 이므로 update 시 미검증
      end
    end
  end

  # ─────────────────────────────────────────────
  # Scopes
  # ─────────────────────────────────────────────
  describe "scopes" do
    let!(:active_membership)  { create(:user_membership, :active) }
    let!(:expired_membership) { create(:user_membership, :expired) }
    let!(:deleted_membership) { create(:user_membership, :deleted) }

    describe ".active" do
      subject(:result) { UserMembership.active }

      it "활성 멤버십을 포함한다" do
        expect(result).to include(active_membership)
      end

      it "만료된 멤버십을 제외한다" do
        expect(result).not_to include(expired_membership)
      end

      it "soft-deleted 멤버십을 제외한다" do
        expect(result).not_to include(deleted_membership)
      end
    end

    describe ".expired" do
      subject(:result) { UserMembership.expired }

      it "만료된 멤버십을 포함한다" do
        expect(result).to include(expired_membership)
      end

      it "활성 멤버십을 제외한다" do
        expect(result).not_to include(active_membership)
      end

      it "soft-deleted 멤버십을 제외한다" do
        expect(result).not_to include(deleted_membership)
      end
    end
  end

  # ─────────────────────────────────────────────
  # Instance Methods
  # ─────────────────────────────────────────────
  describe "#active?" do
    it "삭제되지 않고 만료되지 않은 경우 true를 반환한다" do
      membership = build(:user_membership, :active)
      expect(membership).to be_active
    end

    it "만료된 경우 false를 반환한다" do
      membership = build(:user_membership, :expired)
      expect(membership).not_to be_active
    end

    it "soft-deleted인 경우 false를 반환한다" do
      membership = build(:user_membership, :deleted)
      expect(membership).not_to be_active
    end

    it "expires_at이 정확히 현재 시각이면 false를 반환한다" do
      travel_to(Time.zone.parse("2026-01-15 12:00:00")) do
        membership = build(:user_membership,
                           starts_at:  1.hour.ago,
                           expires_at: Time.current)  # 경계값
        expect(membership).not_to be_active
      end
    end
  end

  describe "#allows?" do
    let(:premium_plan) { create(:membership_plan, :premium) }
    let(:basic_plan)   { create(:membership_plan, :basic) }

    context "프리미엄 플랜 (모든 기능 포함)" do
      subject(:membership) { build(:user_membership, membership_plan: premium_plan) }

      it("learning을 허용한다")      { expect(membership.allows?(:learning)).to be true }
      it("conversation을 허용한다")  { expect(membership.allows?(:conversation)).to be true }
      it("analysis을 허용한다")      { expect(membership.allows?(:analysis)).to be true }
    end

    context "베이직 플랜 (learning만 포함)" do
      subject(:membership) { build(:user_membership, membership_plan: basic_plan) }

      it("learning을 허용한다")          { expect(membership.allows?(:learning)).to be true }
      it("conversation을 허용하지 않는다") { expect(membership.allows?(:conversation)).to be false }
      it("analysis을 허용하지 않는다")    { expect(membership.allows?(:analysis)).to be false }
    end
  end

  describe "#soft_delete!" do
    let!(:membership) { create(:user_membership, :active) }

    it "deleted_at을 현재 시각으로 설정한다" do
      freeze_time do
        membership.soft_delete!
        expect(membership.reload.deleted_at).to be_within(1.second).of(Time.current)
      end
    end

    it "DB에 반영된다" do
      membership.soft_delete!
      expect(membership.reload.deleted_at).not_to be_nil
    end

    it "active? 가 false가 된다" do
      membership.soft_delete!
      expect(membership).not_to be_active
    end

    it ".active 스코프에서 제외된다" do
      membership.soft_delete!
      expect(UserMembership.active).not_to include(membership)
    end
  end

  describe "#days_remaining" do
    context "활성 멤버십" do
      it "남은 일수를 올림(ceil)하여 반환한다" do
        travel_to(Time.zone.parse("2026-01-01 12:00:00")) do
          # 18.5일 남은 상황 → ceil → 19
          membership = build(:user_membership,
                             starts_at:  1.day.ago,
                             expires_at: 17.5.days.from_now)
          expect(membership.days_remaining).to eq(18)
        end
      end

      it "만료 당일(1일 미만) 남으면 1을 반환한다" do
        travel_to(Time.zone.parse("2026-01-31 12:00:00")) do
          membership = build(:user_membership,
                             starts_at:  30.days.ago,
                             expires_at: 1.hour.from_now)
          expect(membership.days_remaining).to eq(1)
        end
      end
    end

    context "만료된 멤버십" do
      it "0을 반환한다" do
        membership = build(:user_membership, :expired)
        expect(membership.days_remaining).to eq(0)
      end
    end

    context "soft-deleted 멤버십" do
      it "0을 반환한다" do
        membership = build(:user_membership, :deleted)
        expect(membership.days_remaining).to eq(0)
      end
    end
  end

  # ─────────────────────────────────────────────
  # expires_at 계산 (MembershipPlan#expires_at_from)
  # ─────────────────────────────────────────────
  describe "만료일 계산 (MembershipPlan#expires_at_from)" do
    it "starts_at + duration_days로 계산된다" do
      plan = create(:membership_plan, :premium, duration_days: 60)
      starts = Time.zone.parse("2026-01-01 00:00:00")
      expect(plan.expires_at_from(starts)).to eq(starts + 60.days)
    end

    it "MembershipGrantService가 올바른 expires_at을 설정한다" do
      user = create(:user)
      plan = create(:membership_plan, :basic, duration_days: 30)
      starts_at = Time.zone.parse("2026-06-01 00:00:00")

      result = MembershipGrantService.call(
        user:            user,
        membership_plan: plan,
        granted_by:      :admin,
        starts_at:       starts_at
      )

      expect(result.membership.expires_at).to eq(starts_at + 30.days)
    end
  end
end
