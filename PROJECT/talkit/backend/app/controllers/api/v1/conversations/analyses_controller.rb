module Api
  module V1
    module Conversations
      # 대화 내용을 분석해 학습 피드백을 생성하는 컨트롤러
      class AnalysesController < Api::V1::ApplicationController
        def create
          return unless require_feature!(:analysis)

          messages = analysis_params[:messages].to_a.map(&:to_h)
          return render_error(:unprocessable_entity, "messages_required") if messages.blank?

          analysis = Ai::AnalysisService.new(messages: messages).analyze
          render json: { analysis: analysis }
        rescue => e
          Rails.logger.error("AnalysesController error: #{e.class}: #{e.message}")
          render_error(:service_unavailable, "analysis_unavailable")
        end

        private

        def analysis_params
          params.permit(messages: %i[role content])
        end
      end
    end
  end
end
