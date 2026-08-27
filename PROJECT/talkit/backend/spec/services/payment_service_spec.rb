# PaymentService의 결제 성공/실패, 트랜잭션 원자성, 멤버십 부여 연동을 검증하는 스펙
require "rails_helper"

RSpec.describe PaymentService do
  subject(:service) do
    described_class.new(
      user:            user,
      membership_plan: plan,
      card_token:      card_token,
      gateway:         gateway
    )
  end

  let(:user)       { create(:user) }
  let(:plan)       { create(:membership_plan, :premium) }
  let(:card_token) { "tok_valid" }
  let(:gateway)    { instance_double(PgGateway::MockPgClient) }

  # 성공 응답 헬퍼
  let(:success_response) do
    { success: true, transaction_id: "mock_txn_001", amount_cents: plan.price_cents, charged_at: Time.current.iso8601 }
  end

  # 실패 응답 헬퍼
  let(:failure_response) { { success: false, error: "insufficient_funds" } }

  # ─────────────────────────────────────────────
  # 결제 성공 경로
  # ─────────────────────────────────────────────
  describe "#call — 결제 성공" do
    before { allow(gateway).to receive(:charge).and_return(success_response) }

    it "[Array<Payment, UserMembership>]를 반환한다" do
      result = service.call
      expect(result).to match([instance_of(Payment), instance_of(UserMembership)])
    end

    it "gateway에 플랜 price_cents와 card_token을 전달한다" do
      service.call
      expect(gateway).to have_received(:charge).with(
        amount_cents: plan.price_cents,
        card_token:   card_token
      )
    end

    describe "Payment 레코드" do
      subject(:payment) { service.call.first }

      it "status가 completed이다" do
        expect(payment.status).to eq("completed")
      end

      it "pg_transaction_id가 설정된다" do
        expect(payment.pg_transaction_id).to eq("mock_txn_001")
      end

      it "pg_response가 저장된다" do
        expect(payment.pg_response).to include("success" => true, "transaction_id" => "mock_txn_001")
      end

      it "amount_cents가 플랜 가격과 같다" do
        expect(payment.amount_cents).to eq(plan.price_cents)
      end

      it "해당 user에 속한다" do
        expect(payment.user).to eq(user)
      end
    end

    describe "UserMembership 레코드" do
      subject(:membership) { service.call.last }

      it "active 상태이다" do
        expect(membership).to be_active
      end

      it "user와 membership_plan이 올바르게 설정된다" do
        expect(membership.user).to eq(user)
        expect(membership.membership_plan).to eq(plan)
      end

      it "granted_by가 payment이다" do
        expect(membership.granted_by).to eq("payment")
      end

      it "payment와 연결된다" do
        payment, membership = service.call
        expect(membership.payment).to eq(payment)
      end

      it "expires_at = starts_at + plan.duration_days" do
        travel_to(Time.zone.parse("2026-01-01 12:00:00")) do
          _, membership = service.call
          expect(membership.expires_at).to be_within(1.second).of(
            Time.current + plan.duration_days.days
          )
        end
      end
    end

    context "기존 활성 멤버십이 존재하는 경우" do
      let!(:existing) { create(:user_membership, :active, user: user, membership_plan: plan) }

      it "기존 멤버십을 soft delete한다" do
        service.call
        expect(existing.reload.deleted_at).not_to be_nil
      end

      it "새 멤버십 1개만 활성 상태가 된다" do
        service.call
        expect(user.user_memberships.active.count).to eq(1)
      end

      it "새 멤버십이 반환된다" do
        _, new_membership = service.call
        expect(new_membership.id).not_to eq(existing.id)
      end
    end
  end

  # ─────────────────────────────────────────────
  # 결제 실패 경로
  # ─────────────────────────────────────────────
  describe "#call — 결제 실패" do
    before { allow(gateway).to receive(:charge).and_return(failure_response) }

    it "PaymentFailedError를 발생시킨다" do
      expect { service.call }.to raise_error(PaymentService::PaymentFailedError)
    end

    it "에러 메시지에 pg_error가 포함된다" do
      expect { service.call }
        .to raise_error(PaymentService::PaymentFailedError, /insufficient_funds/)
    end

    it "Payment 레코드를 failed로 저장한다" do
      service.call rescue nil
      expect(user.payments.last).to have_attributes(status: "failed")
    end

    it "pg_response를 failed Payment에 저장한다" do
      service.call rescue nil
      expect(user.payments.last.pg_response).to include("success" => false, "error" => "insufficient_funds")
    end

    it "UserMembership을 생성하지 않는다" do
      expect { service.call rescue nil }.not_to change(UserMembership, :count)
    end

    it "Payment는 1건 생성된다" do
      expect { service.call rescue nil }.to change(Payment, :count).by(1)
    end
  end

  # ─────────────────────────────────────────────
  # 비활성 플랜
  # ─────────────────────────────────────────────
  describe "#call — 비활성 플랜" do
    let(:plan) { create(:membership_plan, :inactive) }

    before { allow(gateway).to receive(:charge).and_return(success_response) }

    it "PG 청구 후 MembershipGrantService::PlanInactiveError가 발생하면 PaymentGrantError로 변환된다" do
      # PG 청구는 성공, MembershipGrantService가 PlanInactiveError를 발생시킴
      expect { service.call }.to raise_error(PaymentService::PaymentGrantError)
    end

    it "payment가 pending 상태로 남는다 (트랜잭션 롤백 확인)" do
      service.call rescue nil
      expect(user.payments.last.status).to eq("pending")
    end
  end

  # ─────────────────────────────────────────────
  # 트랜잭션 원자성: PG 청구 성공 후 DB 실패
  # ─────────────────────────────────────────────
  describe "#call — 트랜잭션 원자성" do
    before do
      allow(gateway).to receive(:charge).and_return(success_response)
      allow(MembershipGrantService).to receive(:call)
        .and_raise(ActiveRecord::RecordInvalid.new(UserMembership.new))
    end

    it "PaymentGrantError를 발생시킨다" do
      expect { service.call }.to raise_error(PaymentService::PaymentGrantError)
    end

    it "payment가 completed 상태로 남지 않는다 (트랜잭션 롤백)" do
      service.call rescue nil
      expect(user.payments.last.status).to eq("pending")
    end

    it "UserMembership이 생성되지 않는다" do
      expect { service.call rescue nil }.not_to change(UserMembership, :count)
    end
  end

  # ─────────────────────────────────────────────
  # Pending Payment 중간 상태 기록
  # ─────────────────────────────────────────────
  describe "#call — pending payment 선 생성" do
    before { allow(gateway).to receive(:charge).and_return(success_response) }

    it "gateway 호출 전에 pending Payment가 존재한다" do
      allow(gateway).to receive(:charge) do
        expect(user.payments.where(status: "pending").count).to eq(1)
        success_response
      end

      service.call
    end
  end
end
