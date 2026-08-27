# OpenAI Whisper API로 음성 파일을 텍스트로 변환(STT)하는 서비스
module Ai
  class SttService
    # Whisper는 무음/노이즈만 있는 오디오에도 "환각"(hallucination) 텍스트를 만들어내는
    # 경우가 있다 (예: "Thank you.", 자막 관용구 반복 등). verbose_json 응답의 세그먼트별
    # no_speech_prob(발화가 없을 확률)를 확인해, 평균이 임계값을 넘으면 텍스트가 있어도
    # 무시하고 빈 문자열을 반환한다 — 유저가 하지 않은 말이 대화에 들어가는 것을 막는다.
    NO_SPEECH_THRESHOLD = 0.6

    def initialize(audio_file:, language: "en")
      @audio_file = audio_file
      @language   = language
      @client     = OpenAI::Client.new(access_token: ENV.fetch("OPENAI_API_KEY"))
    end

    # @return [Hash] { text: String, duration_seconds: Float }
    def transcribe
      response = @client.audio.transcribe(
        parameters: {
          model:           "whisper-1",
          file:            @audio_file,
          language:        @language,
          response_format: "verbose_json"
        }
      )

      segments = response["segments"].to_a
      text = likely_no_speech?(segments) ? "" : response["text"].to_s.strip

      {
        text:             text,
        duration_seconds: response["duration"]&.to_f
      }
    end

    private

    # 세그먼트별 no_speech_prob 평균이 임계값 이상이면 실제 발화가 없었다고 판단
    def likely_no_speech?(segments)
      return true if segments.empty?

      avg_no_speech_prob = segments.sum { |s| s["no_speech_prob"].to_f } / segments.size
      avg_no_speech_prob >= NO_SPEECH_THRESHOLD
    end
  end
end
