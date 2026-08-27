# 멤버십 플랜 목록 조회 API(공개 엔드포인트)의 응답 형식과 활성 필터링을 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "GET /api/v1/membership_plans", type: :request do
  def json
    JSON.parse(response.body)
  end

  describe "인증" do
    it "X-User-Id 헤더 없이도 200을 반환한다 (인증 불필요)" do
      get "/api/v1/membership_plans"
      expect(response).to have_http_status(:ok)
    end
  end

  describe "응답 내용" do
    let!(:basic)    { create(:membership_plan, :basic) }
    let!(:premium)  { create(:membership_plan, :premium) }
    let!(:inactive) { create(:membership_plan, :premium, :inactive, name: "비활성 플랜") }

    it "활성 플랜만 반환한다" do
      get "/api/v1/membership_plans"
      names = json["plans"].map { |p| p["name"] }
      expect(names).to include(basic.name, premium.name)
      expect(names).not_to include(inactive.name)
    end

    it "price_cents 오름차순으로 정렬된다" do
      get "/api/v1/membership_plans"
      prices = json["plans"].map { |p| p["price_cents"] }
      expect(prices).to eq(prices.sort)
    end

    it "플랜의 전체 필드를 포함한다" do
      get "/api/v1/membership_plans"
      plan_json = json["plans"].find { |p| p["id"] == basic.id }
      expect(plan_json).to include(
        "id"            => basic.id,
        "name"          => basic.name,
        "features"      => ["learning"],
        "duration_days" => basic.duration_days,
        "price_cents"   => basic.price_cents,
        "currency"      => basic.currency
      )
    end

    it "프리미엄 플랜은 모든 기능을 포함한다" do
      get "/api/v1/membership_plans"
      plan_json = json["plans"].find { |p| p["id"] == premium.id }
      expect(plan_json["features"]).to contain_exactly("learning", "conversation", "analysis")
    end
  end

  describe "플랜이 하나도 없는 경우" do
    it "빈 배열을 반환한다" do
      get "/api/v1/membership_plans"
      expect(json["plans"]).to eq([])
    end
  end
end
