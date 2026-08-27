# 본인 관심사(interests) 조회/수정 API의 검증 실패 처리를 포함해 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "Api::V1::Me::Interests", type: :request do
  let(:user)    { create(:user) }
  let(:headers) { { "X-User-Id" => user.id.to_s, "Content-Type" => "application/json" } }

  def json
    JSON.parse(response.body)
  end

  describe "GET /api/v1/me/interests" do
    it "200을 반환한다" do
      get "/api/v1/me/interests", headers: headers
      expect(response).to have_http_status(:ok)
    end

    it "저장된 interests를 반환한다" do
      user.update!(interests: %w[tutor_food tutor_travel])
      get "/api/v1/me/interests", headers: headers
      expect(json["interests"]).to match_array(%w[tutor_food tutor_travel])
    end

    it "아직 설정한 적이 없으면 빈 배열을 반환한다" do
      get "/api/v1/me/interests", headers: headers
      expect(json["interests"]).to eq([])
    end

    it "인증 없이는 401을 반환한다" do
      get "/api/v1/me/interests"
      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "PUT /api/v1/me/interests" do
    def put_interests(interests)
      put "/api/v1/me/interests", params: { interests: interests }.to_json, headers: headers
    end

    it "200을 반환하고 interests를 저장한다" do
      put_interests(%w[tutor_music tutor_reading])
      expect(response).to have_http_status(:ok)
      expect(json["interests"]).to match_array(%w[tutor_music tutor_reading])
      expect(user.reload.interests).to match_array(%w[tutor_music tutor_reading])
    end

    it "빈 배열로 덮어쓸 수 있다" do
      user.update!(interests: %w[tutor_food])
      put_interests([])
      expect(json["interests"]).to eq([])
    end

    it "알 수 없는 주제가 포함되면 422를 반환한다" do
      put_interests(%w[tutor_food not_a_real_topic])
      expect(response).to have_http_status(:unprocessable_entity)
      expect(json["error"]).to eq("invalid_params")
    end

    it "기존 interests를 변경하지 않는다 (422인 경우)" do
      user.update!(interests: %w[tutor_food])
      put_interests(%w[not_a_real_topic])
      expect(user.reload.interests).to eq(%w[tutor_food])
    end

    it "인증 없이는 401을 반환한다" do
      put "/api/v1/me/interests", params: { interests: ["tutor_food"] }.to_json,
          headers: { "Content-Type" => "application/json" }
      expect(response).to have_http_status(:unauthorized)
    end
  end
end
