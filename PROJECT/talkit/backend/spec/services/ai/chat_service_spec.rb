# Ai::ChatService의 스트리밍 처리와 system prompt 구성(토픽/관심사/모드별 분기)을 검증하는 스펙
require "rails_helper"

RSpec.describe Ai::ChatService do
  subject(:service) { described_class.new(messages: messages, topic_id: "self_introduction") }

  let(:messages) { [{ role: "user", content: "Hello" }] }
  let(:client)   { instance_double(OpenAI::Client) }

  before do
    allow(OpenAI::Client).to receive(:new).and_return(client)
  end

  describe "#stream" do
    # ruby-openai 7.x부터 stream:은 do...end 블록이 아니라 parameters 안의 Proc/callable이어야
    # 한다. 과거 코드가 `stream: true` + 블록 형태로 호출해 운영 중 ArgumentError가 발생했었다.
    it "parameters[:stream]으로 호출 가능한(callable) 객체를 전달한다" do
      allow(client).to receive(:chat) do |args|
        expect(args[:parameters][:stream]).to respond_to(:call)
      end

      service.stream { |_delta| }

      expect(client).to have_received(:chat)
    end

    it "OpenAI 청크에서 delta content를 추출해 주어진 block에 순서대로 전달한다" do
      received = []
      allow(client).to receive(:chat) do |args|
        stream_proc = args[:parameters][:stream]
        stream_proc.call({ "choices" => [{ "delta" => { "content" => "Hello" } }] }, nil)
        stream_proc.call({ "choices" => [{ "delta" => { "content" => " world" } }] }, nil)
      end

      service.stream { |delta| received << delta }

      expect(received).to eq(["Hello", " world"])
    end

    it "content가 없는 청크(예: role만 담긴 첫 청크)는 block을 호출하지 않는다" do
      received = []
      allow(client).to receive(:chat) do |args|
        stream_proc = args[:parameters][:stream]
        stream_proc.call({ "choices" => [{ "delta" => { "role" => "assistant" } }] }, nil)
      end

      service.stream { |delta| received << delta }

      expect(received).to be_empty
    end

    it "model과 messages를 parameters에 포함한다" do
      allow(client).to receive(:chat) do |args|
        expect(args[:parameters][:model]).to eq("gpt-4o")
        expect(args[:parameters][:messages]).to include(
          hash_including(role: "user", content: "Hello")
        )
      end

      service.stream { |_delta| }
    end
  end

  describe "system prompt 구성" do
    def system_content_for(service)
      content = nil
      allow(client).to receive(:chat) do |args|
        content = args[:parameters][:messages].first[:content]
      end
      service.stream { |_delta| }
      content
    end

    it "topic_id가 주어지면 해당 Topic/Scenario를 사용한다" do
      service = described_class.new(messages: messages, topic_id: "self_introduction")
      content = system_content_for(service)

      expect(content).to include("## Topic")
      expect(content).to include("자기소개하기")
    end

    it "topic_id(롤플레이 등)가 주어지면 시나리오에 집중하라는 지시를 추가한다" do
      service = described_class.new(messages: messages, topic_id: "self_introduction")
      content = system_content_for(service)

      expect(content).to include("Stay focused on this scenario")
      expect(content).to include("gently steer the conversation back")
    end

    it "topic_id가 주어지고 mode가 practice(기본값)이면 피드백 1줄 + 줄바꿈 + 인캐릭터 응답 1줄 구조를 지시한다" do
      service = described_class.new(messages: messages, topic_id: "self_introduction")
      content = system_content_for(service)

      expect(content).to include("put it on its own line first")
      expect(content).to include("then a line break")
      expect(content).to include("your in-character reply on the next line")
    end

    it "topic_id가 주어져도 mode가 live이면 피드백 지시를 추가하지 않고, 일반 교정 규칙도 명시적으로 끈다" do
      service = described_class.new(messages: messages, topic_id: "self_introduction", mode: "live")
      content = system_content_for(service)

      expect(content).to include("Stay focused on this scenario")
      expect(content).not_to include("put it on its own line first")
      expect(content).to include("Do not give any language feedback")
    end

    it "알려지지 않은 mode 값이 오면(오타 등) 조용히 practice로 폴백한다" do
      service = described_class.new(messages: messages, topic_id: "self_introduction", mode: "Practice")
      content = system_content_for(service)

      expect(content).to include("put it on its own line first")
      expect(content).not_to include("Do not give any language feedback")
    end

    it "topic_id가 없으면(자유대화) 시나리오 집중 지시를 추가하지 않는다" do
      service = described_class.new(messages: messages, interests: %w[tutor_food])
      content = system_content_for(service)

      expect(content).not_to include("Stay focused on this scenario")
    end

    it "topic_id가 없고 interests가 있으면 관심사 목록을 사용한다" do
      service = described_class.new(messages: messages, interests: %w[tutor_food tutor_travel])
      content = system_content_for(service)

      expect(content).to include("## User's interests")
      expect(content).to include("음식과 요리")
      expect(content).to include("여행")
    end

    it "topic_id도 interests도 없으면 일반 자유대화로 폴백한다" do
      service = described_class.new(messages: messages)
      content = system_content_for(service)

      expect(content).to include("General conversation")
    end

    it "알 수 없는 topic_id는 무시되고 interests로 폴백한다" do
      service = described_class.new(messages: messages, topic_id: "no_such_topic", interests: %w[tutor_music])
      content = system_content_for(service)

      expect(content).to include("## User's interests")
      expect(content).to include("음악")
    end

    it "interests가 모두 알려지지 않은 topic_id이면(titles가 비어버림) 일반 자유대화로 폴백한다" do
      service = described_class.new(messages: messages, interests: %w[removed_topic_a removed_topic_b])
      content = system_content_for(service)

      expect(content).not_to include("## User's interests")
      expect(content).to include("General conversation")
    end

    it "wrap_up이 true이면 마무리 지시를 추가한다 (세션 30분 한도 도달 시)" do
      service = described_class.new(messages: messages, topic_id: "self_introduction", wrap_up: true)
      content = system_content_for(service)

      expect(content).to include("## Wrap up")
      expect(content).to include("wrap up the conversation")
    end

    it "wrap_up이 false(기본값)이면 마무리 지시를 추가하지 않는다" do
      service = described_class.new(messages: messages, topic_id: "self_introduction")
      content = system_content_for(service)

      expect(content).not_to include("## Wrap up")
    end
  end
end
