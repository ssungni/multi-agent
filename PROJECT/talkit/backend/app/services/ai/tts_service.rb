# OpenAI TTS API로 텍스트를 음성(mp3)으로 변환하는 서비스
module Ai
  class TtsService
    VALID_VOICES  = %w[alloy echo fable onyx nova shimmer].freeze
    DEFAULT_VOICE = "nova"

    # 알 수 없는 voice 값(오타 등)이 들어오면 조용히 기본 voice로 폴백
    def initialize(text:, voice: DEFAULT_VOICE)
      @text   = text
      @voice  = VALID_VOICES.include?(voice.to_s) ? voice.to_s : DEFAULT_VOICE
      @client = OpenAI::Client.new(access_token: ENV.fetch("OPENAI_API_KEY"))
    end

    # @return [String] raw audio binary (mp3)
    def synthesize
      @client.audio.speech(
        parameters: {
          model:           "tts-1",
          input:           @text,
          voice:           @voice,
          response_format: "mp3"
        }
      )
    end
  end
end
