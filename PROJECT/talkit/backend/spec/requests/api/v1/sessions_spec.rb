# 로그인 API의 인증 성공/실패와 이메일 존재 여부 비노출 정책을 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "POST /api/v1/sessions", type: :request do
  def json
    JSON.parse(response.body)
  end

  def post_session(email, password)
    post "/api/v1/sessions",
         params: { email: email, password: password }.to_json,
         headers: { "Content-Type" => "application/json" }
  end

  describe "인증" do
    it "X-User-Id 헤더 없이도 호출 가능하다 (로그인 전이므로 인증 불필요)" do
      create(:user, email: "exists@example.com", password: "password123")
      post_session("exists@example.com", "password123")
      expect(response).to have_http_status(:ok)
    end
  end

  describe "이메일과 비밀번호가 모두 일치하는 경우" do
    let!(:user) { create(:user, email: "exists@example.com", name: "기존유저", password: "password123") }

    it "200을 반환한다" do
      post_session("exists@example.com", "password123")
      expect(response).to have_http_status(:ok)
    end

    it "user 정보를 반환한다" do
      post_session("exists@example.com", "password123")
      expect(json["user"]).to include(
        "id"   => user.id,
        "email" => "exists@example.com",
        "name" => "기존유저"
      )
    end

    it "응답에 password나 password_digest를 포함하지 않는다" do
      post_session("exists@example.com", "password123")
      expect(json["user"]).not_to have_key("password")
      expect(json["user"]).not_to have_key("password_digest")
    end

    it "이메일 대소문자가 달라도 동일 유저로 로그인된다" do
      post_session("EXISTS@Example.com", "password123")
      expect(json["user"]["id"]).to eq(user.id)
    end
  end

  describe "비밀번호가 틀린 경우" do
    before { create(:user, email: "exists@example.com", password: "password123") }

    it "401을 반환한다" do
      post_session("exists@example.com", "wrong-password")
      expect(response).to have_http_status(:unauthorized)
    end

    it "error: invalid_credentials를 반환한다" do
      post_session("exists@example.com", "wrong-password")
      expect(json["error"]).to eq("invalid_credentials")
    end
  end

  describe "존재하지 않는 이메일" do
    it "401을 반환한다 (이메일 존재 여부를 노출하지 않음)" do
      post_session("nobody@example.com", "password123")
      expect(response).to have_http_status(:unauthorized)
    end

    it "error: invalid_credentials를 반환한다 (틀린 비밀번호와 동일한 에러)" do
      post_session("nobody@example.com", "password123")
      expect(json["error"]).to eq("invalid_credentials")
    end
  end

  describe "유효하지 않은 이메일 형식" do
    it "422를 반환한다" do
      post_session("123", "password123")
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "error: invalid_email_format를 반환한다" do
      post_session("not-an-email", "password123")
      expect(json["error"]).to eq("invalid_email_format")
    end

    it "@만 있고 도메인이 없는 경우도 거부한다" do
      post_session("foo@", "password123")
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "유효한 형식(예: 123@gmail.com)은 통과한다" do
      create(:user, email: "123@gmail.com", password: "password123")
      post_session("123@gmail.com", "password123")
      expect(response).to have_http_status(:ok)
    end
  end
end
