# 결제 API의 성공/실패, 플랜 에러, 인증 에러, 트랜잭션 롤백 처리를 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "POST /api/v1/payments", type: :request do
  let(:user)    { create(:user) }
  let(:plan)    { create(:membership_plan, :premium) }
  let(:headers) { { "X-User-Id" => user.id.to_s, "Content-Type" => "application/json" } }

  def post_payment(params = {})
    default = { membership_plan_id: plan.id, card_token: "tok_valid" }
    post "/api/v1/payments", params: default.merge(params).to_json, headers: headers
  end

  def json
    JSON.parse(response.body)
  end

  # ─────────────────────────────────────────────
  # 성공 케이스
  # ─────────────────────────────────────────────
  describe "결제 성공" do
    it "201 Created를 반환한다" do
      post_payment
      expect(response).to have_http_status(:created)
    end

    it "payment 정보를 반환한다" do
      post_payment
      expect(json["payment"]).to include(
        "status"       => "completed",
        "amount_cents" => plan.price_cents,
        "currency"     => "KRW"
      )
    end

    it "membership 정보를 반환한다" do
      post_payment
      expect(json["membership"]).to include(
        "plan_name" => plan.name
      )
      expect(json["membership"]["expires_at"]).to be_present
    end

    it "Payment 레코드가 생성된다" do
      expect { post_payment }.to change(Payment, :count).by(1)
    end

    it "Payment가 completed 상태로 저장된다" do
      post_payment
      expect(Payment.last.status).to eq("completed")
    end

    it "UserMembership이 생성된다" do
      expect { post_payment }.to change(UserMembership, :count).by(1)
    end

    it "생성된 멤버십이 활성 상태이다" do
      post_payment
      expect(user.user_memberships.active.count).to eq(1)
    end

    context "기존 활성 멤버십이 있는 경우" do
      before { create(:user_membership, :active, user: user, membership_plan: plan) }

      it "201을 반환하고 기존 멤버십을 교체한다" do
        post_payment
        expect(response).to have_http_status(:created)
        expect(user.user_memberships.active.count).to eq(1)
      end
    end
  end

  # ─────────────────────────────────────────────
  # 결제 실패 케이스
  # ─────────────────────────────────────────────
  describe "결제 실패 (tok_mock_fail)" do
    it "422 Unprocessable Entity를 반환한다" do
      post_payment(card_token: "tok_mock_fail")
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "error: payment_failed를 반환한다" do
      post_payment(card_token: "tok_mock_fail")
      expect(json["error"]).to eq("payment_failed")
    end

    it "UserMembership이 생성되지 않는다" do
      expect { post_payment(card_token: "tok_mock_fail") }.not_to change(UserMembership, :count)
    end

    it "failed Payment 레코드가 저장된다" do
      expect { post_payment(card_token: "tok_mock_fail") }.to change(Payment, :count).by(1)
      expect(Payment.last.status).to eq("failed")
    end
  end

  describe "결제 실패 (tok_mock_expired)" do
    it "422를 반환한다" do
      post_payment(card_token: "tok_mock_expired")
      expect(response).to have_http_status(:unprocessable_entity)
    end
  end

  # ─────────────────────────────────────────────
  # 플랜 관련 에러
  # ─────────────────────────────────────────────
  describe "존재하지 않는 플랜 ID" do
    it "404 Not Found를 반환한다" do
      post_payment(membership_plan_id: 999_999)
      expect(response).to have_http_status(:not_found)
    end

    it "error: membership_plan_not_found를 반환한다" do
      post_payment(membership_plan_id: 999_999)
      expect(json["error"]).to eq("membership_plan_not_found")
    end
  end

  describe "비활성 플랜 (active: false)" do
    let(:inactive_plan) { create(:membership_plan, :premium, :inactive) }

    it "404 Not Found를 반환한다 (active 스코프로 필터됨)" do
      post "/api/v1/payments",
           params: { membership_plan_id: inactive_plan.id, card_token: "tok_valid" }.to_json,
           headers: headers
      expect(response).to have_http_status(:not_found)
    end
  end

  # ─────────────────────────────────────────────
  # 인증 에러
  # ─────────────────────────────────────────────
  describe "X-User-Id 헤더 없음" do
    it "401 Unauthorized를 반환한다" do
      post "/api/v1/payments",
           params: { membership_plan_id: plan.id, card_token: "tok_valid" }.to_json,
           headers: { "Content-Type" => "application/json" }
      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "존재하지 않는 User ID" do
    it "401 Unauthorized를 반환한다" do
      post "/api/v1/payments",
           params: { membership_plan_id: plan.id, card_token: "tok_valid" }.to_json,
           headers: headers.merge("X-User-Id" => "999999")
      expect(response).to have_http_status(:unauthorized)
    end
  end

  # ─────────────────────────────────────────────
  # 트랜잭션 롤백 (PG 성공 후 DB 실패)
  # ─────────────────────────────────────────────
  describe "PG 청구 성공 후 멤버십 생성 실패" do
    before do
      allow(MembershipGrantService).to receive(:call)
        .and_raise(ActiveRecord::RecordInvalid.new(UserMembership.new))
    end

    it "500 Internal Server Error를 반환한다" do
      post_payment
      expect(response).to have_http_status(:internal_server_error)
    end

    it "error: payment_grant_failed를 반환한다" do
      post_payment
      expect(json["error"]).to eq("payment_grant_failed")
    end

    it "Payment가 completed 상태로 남지 않는다" do
      post_payment
      expect(user.payments.last&.status).to eq("pending")
    end
  end
end
