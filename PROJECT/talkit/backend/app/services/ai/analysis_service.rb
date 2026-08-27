# 대화 transcript를 OpenAI에 보내 한국어 학습 피드백을 생성하는 서비스
module Ai
  class AnalysisService
    SYSTEM_PROMPT = <<~PROMPT.freeze
      You are an encouraging English learning coach reviewing a conversation between
      a student and an AI tutor.

      Based on the conversation transcript, respond in Korean with concise feedback:
      - 잘한 점 (what the student did well)
      - 개선할 점 (one specific area to improve)
      - 핵심 표현 (1-2 expressions worth remembering, with a short usage example)

      Keep the entire response under 6 sentences. Be specific — reference what the
      student actually said rather than generic advice. If the student barely spoke,
      gently encourage them to speak more next time instead of inventing feedback.
    PROMPT

    def initialize(messages:)
      @messages = messages
      @client   = OpenAI::Client.new(access_token: ENV.fetch("OPENAI_API_KEY"))
    end

    # @return [String] 한국어 분석/피드백 텍스트
    def analyze
      response = @client.chat(
        parameters: {
          model:      "gpt-4o-mini",
          messages:   build_messages,
          max_tokens: 350
        }
      )
      response.dig("choices", 0, "message", "content").to_s.strip
    end

    private

    # 대화 메시지 배열을 사람이 읽을 수 있는 transcript로 변환해 분석 요청에 포함
    def build_messages
      transcript = @messages.map { |m| "#{speaker(m["role"])}: #{m["content"]}" }.join("\n")

      [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: "다음은 학생과 AI 튜터의 대화 내용입니다.\n\n#{transcript}\n\n위 대화를 분석해서 피드백을 주세요." }
      ]
    end

    def speaker(role)
      role == "user" ? "학생" : "AI 튜터"
    end
  end
end
