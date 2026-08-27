# 회원가입(사용자 생성) API의 성공/검증 실패/중복 이메일 처리를 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "POST /api/v1/users", type: :request do
  let(:valid_params) do
    {
      email: "new@example.com",
      name: "신규유저",
      phone_number: "010-1234-5678",
      password: "password123"
    }
  end

  def json
    JSON.parse(response.body)
  end

  def post_user(params)
    post "/api/v1/users", params: params.to_json, headers: { "Content-Type" => "application/json" }
  end

  describe "인증" do
    it "X-User-Id 헤더 없이도 호출 가능하다 (가입 전이므로 인증 불필요)" do
      post_user(valid_params)
      expect(response).to have_http_status(:created)
    end
  end

  describe "성공" do
    it "201 Created를 반환한다" do
      post_user(valid_params)
      expect(response).to have_http_status(:created)
    end

    it "생성된 user 정보를 반환한다 (전화번호 포함)" do
      post_user(valid_params)
      expect(json["user"]).to include(
        "email"        => "new@example.com",
        "name"         => "신규유저",
        "phone_number" => "010-1234-5678"
      )
      expect(json["user"]["id"]).to be_present
    end

    it "User 레코드가 1건 생성된다" do
      expect { post_user(valid_params) }.to change(User, :count).by(1)
    end

    it "이메일은 소문자로 저장된다" do
      post_user(valid_params.merge(email: "New@Example.COM"))
      expect(json["user"]["email"]).to eq("new@example.com")
    end

    it "응답에 password나 password_digest를 포함하지 않는다" do
      post_user(valid_params)
      expect(json["user"]).not_to have_key("password")
      expect(json["user"]).not_to have_key("password_digest")
    end
  end

  describe "중복 이메일" do
    before { create(:user, email: "dup@example.com") }

    it "422 Unprocessable Entity를 반환한다" do
      post_user(valid_params.merge(email: "dup@example.com"))
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "대소문자가 달라도 중복으로 처리한다" do
      post_user(valid_params.merge(email: "DUP@example.com"))
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "User가 추가로 생성되지 않는다" do
      expect { post_user(valid_params.merge(email: "dup@example.com")) }.not_to change(User, :count)
    end

    it "error: invalid_params를 반환한다" do
      post_user(valid_params.merge(email: "dup@example.com"))
      expect(json["error"]).to eq("invalid_params")
    end
  end

  describe "유효성 검증 실패" do
    it "email이 없으면 422를 반환한다" do
      post_user(valid_params.merge(email: ""))
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "email 형식이 잘못되면 422를 반환한다" do
      post_user(valid_params.merge(email: "not-an-email"))
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "name이 없으면 422를 반환한다" do
      post_user(valid_params.merge(name: ""))
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "phone_number가 없으면 422를 반환한다" do
      post_user(valid_params.merge(phone_number: ""))
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "password가 없으면 422를 반환한다" do
      post_user(valid_params.merge(password: ""))
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "password가 8자 미만이면 422를 반환한다" do
      post_user(valid_params.merge(password: "short1"))
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "에러 메시지를 message 필드에 포함한다" do
      post_user(valid_params.merge(email: "", name: ""))
      expect(json["message"]).to be_present
    end

    it "유효성 검증 실패 시 User가 생성되지 않는다" do
      expect { post_user(valid_params.merge(email: "")) }.not_to change(User, :count)
    end
  end
end
