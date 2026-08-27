# Ai::AnalysisService의 대화 분석 결과 생성과 transcript 구성을 검증하는 스펙
require "rails_helper"

RSpec.describe Ai::AnalysisService do
  subject(:service) { described_class.new(messages: messages) }

  let(:messages) do
    [
      { "role" => "assistant", "content" => "What's your name?" },
      { "role" => "user", "content" => "My name is Danny." }
    ]
  end
  let(:client) { instance_double(OpenAI::Client) }

  before do
    allow(OpenAI::Client).to receive(:new).and_return(client)
  end

  describe "#analyze" do
    it "OpenAI 응답의 message content를 그대로 반환한다" do
      allow(client).to receive(:chat).and_return(
        { "choices" => [{ "message" => { "content" => "  잘하셨어요!  " } }] }
      )

      expect(service.analyze).to eq("잘하셨어요!")
    end

    it "gpt-4o-mini 모델로 호출한다" do
      allow(client).to receive(:chat) do |args|
        expect(args[:parameters][:model]).to eq("gpt-4o-mini")
        { "choices" => [{ "message" => { "content" => "ok" } }] }
      end

      service.analyze
    end

    it "system prompt와 대화 transcript를 messages에 포함한다" do
      allow(client).to receive(:chat) do |args|
        sent = args[:parameters][:messages]
        expect(sent.first[:role]).to eq("system")
        expect(sent.last[:content]).to include("학생: My name is Danny.")
        expect(sent.last[:content]).to include("AI 튜터: What's your name?")
        { "choices" => [{ "message" => { "content" => "ok" } }] }
      end

      service.analyze
    end
  end
end
