module Api
  module V1
    module Conversations
      # 텍스트를 음성으로 변환(TTS)하는 컨트롤러
      class TtsController < Api::V1::ApplicationController
        def create
          return unless require_feature!(:conversation)

          text = params[:text].to_s.strip
          return render_error(:unprocessable_entity, "text_required") if text.blank?

          audio_data = Ai::TtsService.new(
            text:  text,
            voice: params.fetch(:voice, "nova")
          ).synthesize

          send_data audio_data, type: "audio/mpeg", disposition: "inline"
        rescue => e
          Rails.logger.error("TtsController error: #{e.class}: #{e.message}")
          render_error(:service_unavailable, "tts_unavailable")
        end
      end
    end
  end
end
