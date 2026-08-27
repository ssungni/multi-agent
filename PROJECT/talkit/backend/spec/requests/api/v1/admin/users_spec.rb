# 관리자용 사용자 목록 조회 API의 인증, 페이지네이션, 멤버십 상태 표시를 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "GET /api/v1/admin/users", type: :request do
  let(:admin_headers) { { "X-Admin-Token" => "secret" } }

  def json
    JSON.parse(response.body)
  end

  def find_user_json(id)
    json["users"].find { |u| u["id"] == id }
  end

  describe "인증" do
    it "유효한 X-Admin-Token이면 200을 반환한다" do
      get "/api/v1/admin/users", headers: admin_headers
      expect(response).to have_http_status(:ok)
    end

    it "토큰이 없으면 401을 반환한다" do
      get "/api/v1/admin/users"
      expect(response).to have_http_status(:unauthorized)
    end

    it "토큰이 틀리면 401을 반환한다" do
      get "/api/v1/admin/users", headers: { "X-Admin-Token" => "wrong" }
      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "유저 목록" do
    it "id, email, name을 포함한다" do
      user = create(:user, name: "홍길동")
      get "/api/v1/admin/users", headers: admin_headers
      expect(find_user_json(user.id)).to include("email" => user.email, "name" => "홍길동")
    end

    it "비밀번호 관련 필드를 포함하지 않는다" do
      user = create(:user)
      get "/api/v1/admin/users", headers: admin_headers
      expect(find_user_json(user.id)).not_to have_key("password")
      expect(find_user_json(user.id)).not_to have_key("password_digest")
    end
  end

  describe "활성 멤버십이 있는 유저" do
    let(:user) { create(:user) }
    let(:plan) { create(:membership_plan, :premium) }
    let!(:membership) { create(:user_membership, :active, user: user, membership_plan: plan) }

    it "active_membership에 플랜명과 만료일을 포함한다" do
      get "/api/v1/admin/users", headers: admin_headers
      expect(find_user_json(user.id)["active_membership"]).to include(
        "id" => membership.id, "plan_name" => plan.name
      )
    end

    it "expired_membership은 null이다 (활성 멤버십이 있으므로)" do
      get "/api/v1/admin/users", headers: admin_headers
      expect(find_user_json(user.id)["expired_membership"]).to be_nil
    end
  end

  describe "한 번도 결제하지 않은 유저" do
    let!(:user) { create(:user) }

    it "active_membership과 expired_membership 모두 null이다" do
      get "/api/v1/admin/users", headers: admin_headers
      result = find_user_json(user.id)
      expect(result["active_membership"]).to be_nil
      expect(result["expired_membership"]).to be_nil
    end
  end

  describe "만료된 멤버십만 있는 유저 — '없음'과 구분되어야 함" do
    let(:user) { create(:user) }
    let(:plan) { create(:membership_plan, :premium) }
    let!(:expired_membership) { create(:user_membership, :expired, user: user, membership_plan: plan) }

    it "active_membership은 null이다" do
      get "/api/v1/admin/users", headers: admin_headers
      expect(find_user_json(user.id)["active_membership"]).to be_nil
    end

    it "expired_membership에 만료된 멤버십 정보를 포함한다" do
      get "/api/v1/admin/users", headers: admin_headers
      expect(find_user_json(user.id)["expired_membership"]).to include(
        "id" => expired_membership.id, "plan_name" => plan.name
      )
    end

    context "만료된 멤버십이 여러 개인 경우" do
      let!(:older_expired) do
        create(:user_membership, :expired, user: user,
               starts_at: 120.days.ago, expires_at: 90.days.ago)
      end

      it "가장 최근에 만료된 것을 반환한다" do
        get "/api/v1/admin/users", headers: admin_headers
        expect(find_user_json(user.id)["expired_membership"]["id"]).to eq(expired_membership.id)
      end
    end
  end

  describe "soft-delete된 멤버십만 있는 유저" do
    let(:user) { create(:user) }
    before { create(:user_membership, :deleted, user: user) }

    it "active_membership과 expired_membership 모두 null이다 (시간 만료가 아니라 삭제된 것)" do
      get "/api/v1/admin/users", headers: admin_headers
      result = find_user_json(user.id)
      expect(result["active_membership"]).to be_nil
      expect(result["expired_membership"]).to be_nil
    end
  end

  describe "페이지네이션" do
    it "meta에 total/page/per_page를 포함한다" do
      get "/api/v1/admin/users", headers: admin_headers
      expect(json["meta"]).to include("total", "page", "per_page")
    end
  end
end
