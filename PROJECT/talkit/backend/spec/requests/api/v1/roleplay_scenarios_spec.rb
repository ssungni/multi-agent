# 롤플레이 시나리오 목록 조회 API의 권한 체크(conversation)와 응답 형식을 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "GET /api/v1/roleplay_scenarios", type: :request do
  let(:user)    { create(:user) }
  let(:headers) { { "X-User-Id" => user.id.to_s } }

  def json
    JSON.parse(response.body)
  end

  describe "conversation 권한이 있는 유저 (Premium 플랜)" do
    let(:plan) { create(:membership_plan, :premium) }

    before { create(:user_membership, :active, user: user, membership_plan: plan) }

    it "200을 반환한다" do
      get "/api/v1/roleplay_scenarios", headers: headers
      expect(response).to have_http_status(:ok)
    end

    it "series_title, position 순으로 정렬된 시나리오 목록을 반환한다" do
      create(:roleplay_scenario, series_title: "직장인 필수영어", title: "두번째", position: 2)
      create(:roleplay_scenario, series_title: "직장인 필수영어", title: "첫번째", position: 1)

      get "/api/v1/roleplay_scenarios", headers: headers

      expect(json["roleplay_scenarios"].map { |s| s["title"] }).to eq(%w[첫번째 두번째])
    end

    it "시나리오 필드를 모두 포함한다 (topic_id 포함)" do
      create(:roleplay_scenario,
             series_title: "직장인 필수영어", title: "힘 빼고 영어 잘하기",
             level: "Basic", description: "설명", position: 1, topic_id: "workplace_english")

      get "/api/v1/roleplay_scenarios", headers: headers

      expect(json["roleplay_scenarios"].first).to include(
        "series_title" => "직장인 필수영어",
        "title"        => "힘 빼고 영어 잘하기",
        "level"        => "Basic",
        "topic_id"     => "workplace_english"
      )
    end

    it "Ai::ChatService::TOPICS의 opening/live_opening을 그대로 내려준다 (프론트와의 단일 진실 공급원)" do
      create(:roleplay_scenario, topic_id: "roleplay_us_immigration")
      topic = Ai::ChatService::TOPICS["roleplay_us_immigration"]

      get "/api/v1/roleplay_scenarios", headers: headers

      expect(json["roleplay_scenarios"].first).to include(
        "opening"      => topic[:opening],
        "live_opening" => topic[:live_opening]
      )
    end
  end

  describe "conversation 권한이 없는 유저 (Basic 플랜)" do
    let(:plan) { create(:membership_plan, :basic) }

    before { create(:user_membership, :active, user: user, membership_plan: plan) }

    it "403을 반환한다" do
      get "/api/v1/roleplay_scenarios", headers: headers
      expect(response).to have_http_status(:forbidden)
    end
  end

  describe "인증 없음" do
    it "401을 반환한다" do
      get "/api/v1/roleplay_scenarios"
      expect(response).to have_http_status(:unauthorized)
    end
  end
end
