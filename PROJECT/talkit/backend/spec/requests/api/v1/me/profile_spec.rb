# 본인 프로필 조회 API의 응답 형식과 인증 체크를 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "GET /api/v1/me/profile", type: :request do
  let(:user)    { create(:user, name: "홍길동", phone_number: "010-1234-5678") }
  let(:headers) { { "X-User-Id" => user.id.to_s } }

  def json
    JSON.parse(response.body)
  end

  it "200을 반환한다" do
    get "/api/v1/me/profile", headers: headers
    expect(response).to have_http_status(:ok)
  end

  it "id, email, name, phone_number를 반환한다" do
    get "/api/v1/me/profile", headers: headers
    expect(json).to include(
      "id"           => user.id,
      "email"        => user.email,
      "name"         => "홍길동",
      "phone_number" => "010-1234-5678"
    )
  end

  it "password나 password_digest를 포함하지 않는다" do
    get "/api/v1/me/profile", headers: headers
    expect(json).not_to have_key("password")
    expect(json).not_to have_key("password_digest")
  end

  it "인증 없이는 401을 반환한다" do
    get "/api/v1/me/profile"
    expect(response).to have_http_status(:unauthorized)
  end
end
