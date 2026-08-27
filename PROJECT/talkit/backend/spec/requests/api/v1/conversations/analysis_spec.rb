# 대화 분석(Analysis) API의 성공/검증 실패/예외 처리와 권한 체크를 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "POST /api/v1/conversations/analysis", type: :request do
  let(:user)     { create(:user) }
  let(:plan)     { create(:membership_plan, :premium) }
  let(:headers)  { { "X-User-Id" => user.id.to_s, "Content-Type" => "application/json" } }
  let(:messages) { [{ role: "user", content: "My name is Danny." }] }

  before { create(:user_membership, :active, user: user, membership_plan: plan) }

  def json
    JSON.parse(response.body)
  end

  def post_analysis(params = { messages: messages })
    post "/api/v1/conversations/analysis", params: params.to_json, headers: headers
  end

  describe "성공" do
    before do
      allow_any_instance_of(Ai::AnalysisService).to receive(:analyze).and_return("좋은 피드백입니다.")
    end

    it "200을 반환한다" do
      post_analysis
      expect(response).to have_http_status(:ok)
    end

    it "analysis 텍스트를 반환한다" do
      post_analysis
      expect(json["analysis"]).to eq("좋은 피드백입니다.")
    end
  end

  describe "messages가 비어있는 경우" do
    it "422를 반환한다" do
      post_analysis(messages: [])
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "error: messages_required를 반환한다" do
      post_analysis(messages: [])
      expect(json["error"]).to eq("messages_required")
    end
  end

  describe "analysis 권한이 없는 유저 (Basic 플랜)" do
    let(:plan) { create(:membership_plan, :basic) }

    it "403을 반환한다" do
      post_analysis
      expect(response).to have_http_status(:forbidden)
    end
  end

  describe "AnalysisService가 예외를 던지는 경우" do
    before { allow_any_instance_of(Ai::AnalysisService).to receive(:analyze).and_raise(StandardError, "boom") }

    it "503을 반환한다" do
      post_analysis
      expect(response).to have_http_status(:service_unavailable)
    end

    it "error: analysis_unavailable을 반환한다" do
      post_analysis
      expect(json["error"]).to eq("analysis_unavailable")
    end
  end

  describe "인증 없음" do
    it "401을 반환한다" do
      post "/api/v1/conversations/analysis",
           params: { messages: messages }.to_json,
           headers: { "Content-Type" => "application/json" }
      expect(response).to have_http_status(:unauthorized)
    end
  end
end
