# 음성 인식(STT) API의 성공/용량 초과/예외 처리와 권한 체크를 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "POST /api/v1/conversations/stt", type: :request do
  let(:user)    { create(:user) }
  let(:plan)    { create(:membership_plan, :premium) }
  let(:headers) { { "X-User-Id" => user.id.to_s } }

  before { create(:user_membership, :active, user: user, membership_plan: plan) }

  def json
    JSON.parse(response.body)
  end

  def audio_upload
    file = Tempfile.new(["audio", ".webm"])
    file.write("fake audio bytes")
    file.rewind
    Rack::Test::UploadedFile.new(file.path, "audio/webm")
  end

  describe "성공" do
    before do
      allow_any_instance_of(Ai::SttService).to receive(:transcribe).and_return(
        { text: "Hello there", duration_seconds: 1.2 }
      )
    end

    it "200을 반환한다" do
      post "/api/v1/conversations/stt", params: { audio: audio_upload }, headers: headers
      expect(response).to have_http_status(:ok)
    end

    it "text와 duration_seconds를 반환한다" do
      post "/api/v1/conversations/stt", params: { audio: audio_upload }, headers: headers
      expect(json).to eq("text" => "Hello there", "duration_seconds" => 1.2)
    end
  end

  # Whisper의 무음/노이즈 환각(hallucination)을 SttService가 빈 문자열로 걸러낸 경우,
  # 컨트롤러는 이를 그대로(에러 없이) 통과시켜야 프론트가 "발화 없음"으로 정상 처리한다.
  describe "SttService가 환각을 걸러내 빈 텍스트를 반환하는 경우" do
    before do
      allow_any_instance_of(Ai::SttService).to receive(:transcribe).and_return(
        { text: "", duration_seconds: 0.4 }
      )
    end

    it "200과 빈 text를 그대로 반환한다" do
      post "/api/v1/conversations/stt", params: { audio: audio_upload }, headers: headers
      expect(response).to have_http_status(:ok)
      expect(json["text"]).to eq("")
    end
  end

  describe "audio 파라미터가 없는 경우" do
    it "422를 반환한다" do
      post "/api/v1/conversations/stt", params: {}, headers: headers
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "error: invalid_audio를 반환한다" do
      post "/api/v1/conversations/stt", params: {}, headers: headers
      expect(json["error"]).to eq("invalid_audio")
    end
  end

  describe "audio 파일이 용량 한도(25MB)를 초과하는 경우" do
    def oversized_audio_upload
      file = Tempfile.new(["audio", ".webm"])
      allow_any_instance_of(ActionDispatch::Http::UploadedFile).to receive(:size)
        .and_return(25.megabytes + 1)
      Rack::Test::UploadedFile.new(file.path, "audio/webm")
    end

    it "422와 invalid_audio를 반환한다 (SttService를 호출하지 않음)" do
      expect(Ai::SttService).not_to receive(:new)
      post "/api/v1/conversations/stt", params: { audio: oversized_audio_upload }, headers: headers
      expect(response).to have_http_status(:unprocessable_entity)
      expect(json["error"]).to eq("invalid_audio")
    end
  end

  describe "conversation 권한이 없는 유저 (Basic 플랜)" do
    let(:plan) { create(:membership_plan, :basic) }

    it "403을 반환한다" do
      post "/api/v1/conversations/stt", params: { audio: audio_upload }, headers: headers
      expect(response).to have_http_status(:forbidden)
    end
  end

  describe "SttService가 예외를 던지는 경우" do
    before { allow_any_instance_of(Ai::SttService).to receive(:transcribe).and_raise(StandardError, "boom") }

    it "503을 반환한다" do
      post "/api/v1/conversations/stt", params: { audio: audio_upload }, headers: headers
      expect(response).to have_http_status(:service_unavailable)
    end

    it "error: stt_unavailable을 반환한다" do
      post "/api/v1/conversations/stt", params: { audio: audio_upload }, headers: headers
      expect(json["error"]).to eq("stt_unavailable")
    end
  end

  describe "인증 없음" do
    it "401을 반환한다" do
      post "/api/v1/conversations/stt", params: { audio: audio_upload }
      expect(response).to have_http_status(:unauthorized)
    end
  end
end
