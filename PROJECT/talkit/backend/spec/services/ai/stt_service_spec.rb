# Ai::SttService의 음성 인식 결과 처리와 무음/환각 텍스트 필터링을 검증하는 스펙
require "rails_helper"

RSpec.describe Ai::SttService do
  subject(:service) { described_class.new(audio_file: audio_file) }

  let(:audio_file)  { double("uploaded_file") }
  let(:client)      { instance_double(OpenAI::Client) }
  let(:audio_api)   { instance_double(OpenAI::Audio) }

  before do
    allow(OpenAI::Client).to receive(:new).and_return(client)
    allow(client).to receive(:audio).and_return(audio_api)
  end

  describe "#transcribe" do
    it "정상적으로 발화가 감지되면 텍스트를 그대로 반환한다" do
      allow(audio_api).to receive(:transcribe).and_return(
        {
          "text"     => "Hello, my name is Danny.",
          "duration" => 2.4,
          "segments" => [{ "no_speech_prob" => 0.02 }]
        }
      )

      result = service.transcribe

      expect(result[:text]).to eq("Hello, my name is Danny.")
      expect(result[:duration_seconds]).to eq(2.4)
    end

    # Whisper는 무음/노이즈에도 그럴듯한 문장을 "환각"으로 만들어낸다 — 평균 no_speech_prob가
    # 높으면 텍스트가 채워져 있어도 무시해야, 유저가 하지 않은 말이 대화에 들어가지 않는다.
    it "no_speech_prob 평균이 임계값 이상이면 텍스트가 있어도 빈 문자열로 처리한다 (환각 방지)" do
      allow(audio_api).to receive(:transcribe).and_return(
        {
          "text"     => "Thank you for watching!",
          "duration" => 1.1,
          "segments" => [{ "no_speech_prob" => 0.85 }]
        }
      )

      result = service.transcribe

      expect(result[:text]).to eq("")
    end

    it "세그먼트가 여러 개일 때 평균 no_speech_prob로 판단한다" do
      allow(audio_api).to receive(:transcribe).and_return(
        {
          "text"     => "okay",
          "duration" => 3.0,
          "segments" => [
            { "no_speech_prob" => 0.9 },
            { "no_speech_prob" => 0.9 },
            { "no_speech_prob" => 0.1 }
          ]
        }
      )
      # 평균 = (0.9+0.9+0.1)/3 ≈ 0.633 → 임계값(0.6) 이상이므로 환각으로 처리
      result = service.transcribe

      expect(result[:text]).to eq("")
    end

    it "세그먼트가 비어있으면 발화가 없었다고 보고 빈 문자열을 반환한다" do
      allow(audio_api).to receive(:transcribe).and_return(
        { "text" => "music playing", "duration" => 0.5, "segments" => [] }
      )

      result = service.transcribe

      expect(result[:text]).to eq("")
    end

    it "segments 키가 없으면(nil) 발화가 없었다고 보고 빈 문자열을 반환한다" do
      allow(audio_api).to receive(:transcribe).and_return(
        { "text" => "hmm", "duration" => 0.3 }
      )

      result = service.transcribe

      expect(result[:text]).to eq("")
    end

    it "no_speech_prob가 낮은(확신 있는) 발화는 텍스트를 그대로 반환한다" do
      allow(audio_api).to receive(:transcribe).and_return(
        {
          "text"     => "What time is it?",
          "duration" => 1.5,
          "segments" => [{ "no_speech_prob" => 0.05 }, { "no_speech_prob" => 0.1 }]
        }
      )

      result = service.transcribe

      expect(result[:text]).to eq("What time is it?")
    end

    it "whisper-1 모델과 verbose_json 포맷으로 호출한다" do
      allow(audio_api).to receive(:transcribe) do |args|
        expect(args[:parameters][:model]).to eq("whisper-1")
        expect(args[:parameters][:response_format]).to eq("verbose_json")
        expect(args[:parameters][:file]).to eq(audio_file)
        { "text" => "ok", "segments" => [{ "no_speech_prob" => 0.0 }] }
      end

      service.transcribe
    end
  end
end
