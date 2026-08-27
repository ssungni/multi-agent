# AI 채팅 SSE 스트리밍 API의 응답 형식, 파라미터 전달, 권한 체크를 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "POST /api/v1/conversations/chat", type: :request do
  let(:user)     { create(:user) }
  let(:plan)     { create(:membership_plan, :premium) }
  let(:headers)  { { "X-User-Id" => user.id.to_s, "Content-Type" => "application/json" } }
  let(:messages) { [{ role: "user", content: "Hello" }] }

  before { create(:user_membership, :active, user: user, membership_plan: plan) }

  def post_chat
    post "/api/v1/conversations/chat",
         params: { messages: messages, topic_id: "self_introduction" }.to_json,
         headers: headers
  end

  describe "성공 — SSE 응답 형식" do
    before do
      allow_any_instance_of(Ai::ChatService).to receive(:stream) do |_instance, &block|
        block.call("Hello ")
        block.call("world.")
      end
    end

    it "200과 text/event-stream Content-Type을 반환한다" do
      post_chat
      expect(response).to have_http_status(:ok)
      expect(response.content_type).to include("text/event-stream")
    end

    # 프론트엔드 useSSEChat이 `parsed.delta`로 파싱하므로(OpenAI raw chunk 형식이 아님),
    # 백엔드가 이 평탄 구조를 깨면 프론트 전체 대화가 조용히 끊긴다 — 그 계약을 고정한다.
    it '각 delta를 "data: {"delta":...}\n\n" 평탄 구조로 내려준다' do
      post_chat
      expect(response.body).to include(%(data: {"delta":"Hello "}\n\n))
      expect(response.body).to include(%(data: {"delta":"world."}\n\n))
    end

    it '스트림 끝에 "data: [DONE]\n\n"을 보낸다' do
      post_chat
      expect(response.body).to end_with("data: [DONE]\n\n")
    end
  end

  describe "topic_id가 없을 때 — 현재 유저의 저장된 interests를 ChatService에 전달한다" do
    before do
      user.update!(interests: %w[tutor_food tutor_music])
      allow_any_instance_of(Ai::ChatService).to receive(:stream)
    end

    it "Ai::ChatService.new에 현재 유저의 interests를 넘긴다" do
      expect(Ai::ChatService).to receive(:new).with(
        hash_including(interests: %w[tutor_food tutor_music])
      ).and_call_original

      post "/api/v1/conversations/chat",
           params: { messages: messages }.to_json,
           headers: headers
    end
  end

  describe "wrap_up 파라미터" do
    before { allow_any_instance_of(Ai::ChatService).to receive(:stream) }

    it "wrap_up: true를 보내면 Ai::ChatService.new에 wrap_up: true가 전달된다" do
      expect(Ai::ChatService).to receive(:new).with(
        hash_including(wrap_up: true)
      ).and_call_original

      post "/api/v1/conversations/chat",
           params: { messages: messages, topic_id: "self_introduction", wrap_up: true }.to_json,
           headers: headers
    end

    it "wrap_up을 보내지 않으면 wrap_up: false가 전달된다 (기본값)" do
      expect(Ai::ChatService).to receive(:new).with(
        hash_including(wrap_up: false)
      ).and_call_original

      post_chat
    end
  end

  describe "mode 파라미터" do
    before { allow_any_instance_of(Ai::ChatService).to receive(:stream) }

    it "mode: live를 보내면 Ai::ChatService.new에 mode: \"live\"가 전달된다" do
      expect(Ai::ChatService).to receive(:new).with(
        hash_including(mode: "live")
      ).and_call_original

      post "/api/v1/conversations/chat",
           params: { messages: messages, topic_id: "self_introduction", mode: "live" }.to_json,
           headers: headers
    end

    it "mode를 보내지 않으면 mode: \"practice\"가 전달된다 (기본값)" do
      expect(Ai::ChatService).to receive(:new).with(
        hash_including(mode: "practice")
      ).and_call_original

      post_chat
    end
  end

  describe "conversation 권한이 없는 유저 (Basic 플랜)" do
    let(:plan) { create(:membership_plan, :basic) }

    it "403을 반환한다" do
      post_chat
      expect(response).to have_http_status(:forbidden)
    end
  end

  describe "인증 없음" do
    it "401을 반환한다" do
      post "/api/v1/conversations/chat", params: { messages: messages }.to_json,
           headers: { "Content-Type" => "application/json" }
      expect(response).to have_http_status(:unauthorized)
    end
  end
end
