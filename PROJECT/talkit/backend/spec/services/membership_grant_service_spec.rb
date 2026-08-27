# MembershipGrantService의 멤버십 부여, 기존 멤버십 교체, 비활성 플랜 처리를 검증하는 스펙
require "rails_helper"

RSpec.describe MembershipGrantService do
  subject(:result) { described_class.call(**params) }

  let(:user)   { create(:user) }
  let(:plan)   { create(:membership_plan, :premium) }
  let(:params) { { user: user, membership_plan: plan, granted_by: :admin } }

  describe ".call" do
    it "Result 객체를 반환한다" do
      expect(result).to be_a(described_class::Result)
    end
  end

  # ─────────────────────────────────────────────
  # 성공 경로
  # ─────────────────────────────────────────────
  describe "#call — 성공 경로" do
    it "UserMembership을 1건 생성한다" do
      expect { result }.to change(UserMembership, :count).by(1)
    end

    it "user와 membership_plan이 올바르게 설정된다" do
      membership = result.membership
      expect(membership.user).to eq(user)
      expect(membership.membership_plan).to eq(plan)
    end

    it "granted_by가 올바르게 설정된다" do
      expect(result.membership.granted_by).to eq("admin")
    end

    it "생성된 멤버십은 활성 상태이다" do
      expect(result.membership).to be_active
    end

    it "starts_at 기본값은 호출 시점의 Time.current이다" do
      travel_to(Time.zone.parse("2026-01-01 12:00:00")) do
        membership = described_class.call(**params).membership
        expect(membership.starts_at).to be_within(1.second).of(Time.current)
      end
    end

    it "starts_at을 명시하면 그대로 사용한다" do
      starts_at  = Time.zone.parse("2026-03-01 00:00:00")
      membership = described_class.call(**params, starts_at: starts_at).membership
      expect(membership.starts_at).to eq(starts_at)
    end

    it "expires_at = starts_at + plan.duration_days로 계산된다" do
      starts_at  = Time.zone.parse("2026-03-01 00:00:00")
      membership = described_class.call(**params, starts_at: starts_at).membership
      expect(membership.expires_at).to eq(starts_at + plan.duration_days.days)
    end

    it "granted_by_admin_id를 설정할 수 있다" do
      membership = described_class.call(**params, granted_by_admin_id: 99).membership
      expect(membership.granted_by_admin_id).to eq(99)
    end

    it "payment를 연결할 수 있다 (granted_by: :payment)" do
      payment    = create(:payment, :completed, user: user, membership_plan: plan)
      membership = described_class.call(
        user: user, membership_plan: plan, granted_by: :payment, payment: payment
      ).membership
      expect(membership.payment).to eq(payment)
    end
  end

  # ─────────────────────────────────────────────
  # Result#replaced?
  # ─────────────────────────────────────────────
  describe "#call — Result#replaced?" do
    context "기존 활성 멤버십이 없는 경우" do
      it "previous_membership이 nil이다" do
        expect(result.previous_membership).to be_nil
      end

      it "replaced?가 false를 반환한다" do
        expect(result.replaced?).to be false
      end
    end

    context "기존 활성 멤버십이 있는 경우" do
      let!(:existing) { create(:user_membership, :active, user: user) }

      it "기존 멤버십을 soft delete한다" do
        result
        expect(existing.reload.deleted_at).not_to be_nil
      end

      it "previous_membership으로 기존 멤버십을 반환한다" do
        expect(result.previous_membership).to eq(existing)
      end

      it "replaced?가 true를 반환한다" do
        expect(result.replaced?).to be true
      end

      it "새 멤버십 1개만 활성 상태로 남는다" do
        result
        expect(user.user_memberships.active.count).to eq(1)
      end

      it "새로 생성된 멤버십이 반환된다 (기존과 다른 id)" do
        expect(result.membership.id).not_to eq(existing.id)
      end
    end

    context "여러 개의 기존 활성 멤버십이 있는 경우 (데이터 정합성 이슈 방어)" do
      let!(:existing_1) { create(:user_membership, :active, user: user) }
      let!(:existing_2) do
        m = build(:user_membership, user: user, starts_at: 1.day.ago, expires_at: 20.days.from_now)
        m.save!(validate: false) # 중복 활성 멤버십 validation을 우회해 데이터 정합성 문제를 시뮬레이션
        m
      end

      it "모든 기존 활성 멤버십을 soft delete한다" do
        result
        expect(existing_1.reload.deleted_at).not_to be_nil
        expect(existing_2.reload.deleted_at).not_to be_nil
      end

      it "새 멤버십 1개만 활성 상태로 남는다" do
        result
        expect(user.user_memberships.active.count).to eq(1)
      end
    end
  end

  # ─────────────────────────────────────────────
  # 비활성 플랜
  # ─────────────────────────────────────────────
  describe "#call — 비활성 플랜" do
    let(:plan) { create(:membership_plan, :inactive) }

    it "PlanInactiveError를 발생시킨다" do
      expect { result }.to raise_error(MembershipGrantService::PlanInactiveError)
    end

    it "UserMembership을 생성하지 않는다" do
      expect { result rescue nil }.not_to change(UserMembership, :count)
    end

    it "기존 활성 멤버십을 건드리지 않는다 (active? 검사가 트랜잭션보다 먼저 실행됨)" do
      existing = create(:user_membership, :active, user: user, membership_plan: create(:membership_plan, :basic))
      expect { result rescue nil }.not_to change { existing.reload.deleted_at }
    end
  end
end
