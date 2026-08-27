# 토픽 목록 조회 API의 권한 체크(learning)와 응답 형식을 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "GET /api/v1/topics", type: :request do
  let(:user)    { create(:user) }
  let(:headers) { { "X-User-Id" => user.id.to_s } }

  def json
    JSON.parse(response.body)
  end

  describe "learning 권한이 있는 유저 (Basic 플랜)" do
    let(:plan) { create(:membership_plan, :basic) }

    before { create(:user_membership, :active, user: user, membership_plan: plan) }

    it "200을 반환한다" do
      get "/api/v1/topics", headers: headers
      expect(response).to have_http_status(:ok)
    end

    it "position 순으로 정렬된 토픽 목록을 반환한다" do
      create(:topic, title: "B", position: 2)
      create(:topic, title: "A", position: 1)

      get "/api/v1/topics", headers: headers

      expect(json["topics"].map { |t| t["title"] }).to eq(%w[A B])
    end

    it "토픽 필드를 모두 포함한다" do
      create(:topic,
             title: "South Korea Keeps World Cup Hopes Alive",
             category: "월드컵",
             image_url: "/images/topics/01_wordcup.jpeg",
             english_1: "English paragraph 1", korean_1: "한국어 문단 1",
             english_2: "English paragraph 2", korean_2: "한국어 문단 2")

      get "/api/v1/topics", headers: headers

      expect(json["topics"].first).to include(
        "title"     => "South Korea Keeps World Cup Hopes Alive",
        "category"  => "월드컵",
        "image_url" => "/images/topics/01_wordcup.jpeg",
        "english_1" => "English paragraph 1",
        "korean_1"  => "한국어 문단 1",
        "english_2" => "English paragraph 2",
        "korean_2"  => "한국어 문단 2"
      )
    end
  end

  describe "learning 권한이 없는 유저 (멤버십 없음)" do
    it "403을 반환한다" do
      get "/api/v1/topics", headers: headers
      expect(response).to have_http_status(:forbidden)
    end

    it "error: feature_not_allowed를 반환한다" do
      get "/api/v1/topics", headers: headers
      expect(json["error"]).to eq("feature_not_allowed")
    end
  end

  describe "인증 없음" do
    it "401을 반환한다" do
      get "/api/v1/topics"
      expect(response).to have_http_status(:unauthorized)
    end
  end
end
