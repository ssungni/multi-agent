module Api
  module V1
    module Conversations
      # 음성 파일을 텍스트로 변환(STT)하는 컨트롤러
      class SttController < Api::V1::ApplicationController
        # OpenAI Whisper API 자체의 업로드 한도(25MB)에 맞춘다 — 그보다 큰 파일은
        # 어차피 SttService 호출이 실패하므로, 미리 걸러내 불필요한 외부 API 호출을 막는다.
        MAX_AUDIO_SIZE = 25.megabytes

        def create
          return unless require_feature!(:conversation)
          return render_error(:unprocessable_entity, "invalid_audio") unless valid_audio?

          result = Ai::SttService.new(
            audio_file: params[:audio],
            language:   params.fetch(:language, "en")
          ).transcribe

          render json: result
        rescue => e
          Rails.logger.error("SttController error: #{e.class}: #{e.message}")
          render_error(:service_unavailable, "stt_unavailable")
        end

        private

        def valid_audio?
          audio = params[:audio]
          audio.present? && audio.respond_to?(:read) && audio.size.to_i <= MAX_AUDIO_SIZE
        end
      end
    end
  end
end
