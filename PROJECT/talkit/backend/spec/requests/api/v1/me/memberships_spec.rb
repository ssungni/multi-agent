# 본인 멤버십 조회 API의 활성/만료/없음 상태 구분 응답을 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "GET /api/v1/me/membership", type: :request do
  let(:user)    { create(:user) }
  let(:headers) { { "X-User-Id" => user.id.to_s } }

  def json
    JSON.parse(response.body)
  end

  describe "활성 멤버십이 있는 경우" do
    let(:plan)        { create(:membership_plan, :premium) }
    let!(:membership) { create(:user_membership, :active, user: user, membership_plan: plan) }

    it "200을 반환한다" do
      get "/api/v1/me/membership", headers: headers
      expect(response).to have_http_status(:ok)
    end

    it "멤버십 정보를 반환한다" do
      get "/api/v1/me/membership", headers: headers
      expect(json["membership"]).to include(
        "id"   => membership.id,
        "plan" => {
          "id"       => plan.id,
          "name"     => plan.name,
          "features" => %w[learning conversation analysis]
        }
      )
    end

    it "starts_at / expires_at / days_remaining을 포함한다" do
      get "/api/v1/me/membership", headers: headers
      expect(json["membership"]["starts_at"]).to be_present
      expect(json["membership"]["expires_at"]).to be_present
      expect(json["membership"]["days_remaining"]).to be_a(Integer)
    end

    context "활성 멤버십이 여러 개 존재하는 경우 (데이터 정합성 이슈)" do
      let!(:older) do
        m = build(:user_membership, user: user, membership_plan: plan,
                   starts_at: 5.days.ago, expires_at: 25.days.from_now,
                   created_at: 2.days.ago)
        m.save!(validate: false)
        m
      end

      it "가장 최근에 생성된 멤버십을 반환한다" do
        get "/api/v1/me/membership", headers: headers
        expect(json["membership"]["id"]).to eq(membership.id)
      end
    end
  end

  describe "활성 멤버십이 없는 경우 (한 번도 결제하지 않음)" do
    it "404를 반환한다" do
      get "/api/v1/me/membership", headers: headers
      expect(response).to have_http_status(:not_found)
    end

    it "error: no_active_membership을 반환한다" do
      get "/api/v1/me/membership", headers: headers
      expect(json["error"]).to eq("no_active_membership")
    end

    it "expired_membership은 null이다 (과거 멤버십 자체가 없음)" do
      get "/api/v1/me/membership", headers: headers
      expect(json["expired_membership"]).to be_nil
    end
  end

  describe "만료된 멤버십만 있는 경우" do
    let(:plan) { create(:membership_plan, :premium) }
    let!(:expired_membership) { create(:user_membership, :expired, user: user, membership_plan: plan) }

    it "404를 반환한다" do
      get "/api/v1/me/membership", headers: headers
      expect(response).to have_http_status(:not_found)
    end

    it "expired_membership에 만료된 멤버십 정보를 포함한다 (만료됨/없음을 구분 가능)" do
      get "/api/v1/me/membership", headers: headers
      expect(json["expired_membership"]).to include(
        "id"   => expired_membership.id,
        "plan" => { "id" => plan.id, "name" => plan.name, "features" => %w[learning conversation analysis] }
      )
    end

    context "만료된 멤버십이 여러 개인 경우" do
      let!(:older_expired) do
        create(:user_membership, :expired, user: user,
               starts_at: 120.days.ago, expires_at: 90.days.ago)
      end

      it "가장 최근에 만료된 것을 반환한다" do
        get "/api/v1/me/membership", headers: headers
        expect(json["expired_membership"]["id"]).to eq(expired_membership.id)
      end
    end

    context "soft-delete된 멤버십도 있는 경우" do
      let!(:deleted_membership) { create(:user_membership, :deleted, user: user) }

      it "soft-delete된 것은 expired_membership으로 잡히지 않는다" do
        get "/api/v1/me/membership", headers: headers
        expect(json["expired_membership"]["id"]).to eq(expired_membership.id)
      end
    end
  end

  describe "soft-deleted 멤버십만 있는 경우" do
    before { create(:user_membership, :deleted, user: user) }

    it "404를 반환한다" do
      get "/api/v1/me/membership", headers: headers
      expect(response).to have_http_status(:not_found)
    end
  end

  describe "인증 에러" do
    it "X-User-Id 헤더 없으면 401을 반환한다" do
      get "/api/v1/me/membership"
      expect(response).to have_http_status(:unauthorized)
    end

    it "존재하지 않는 User ID면 401을 반환한다" do
      get "/api/v1/me/membership", headers: { "X-User-Id" => "999999" }
      expect(response).to have_http_status(:unauthorized)
    end
  end
end
