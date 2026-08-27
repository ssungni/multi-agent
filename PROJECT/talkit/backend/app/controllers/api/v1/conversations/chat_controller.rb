module Api
  module V1
    module Conversations
      # AI와의 대화를 SSE(Server-Sent Events)로 실시간 스트리밍하는 컨트롤러
      class ChatController < Api::V1::ApplicationController
        include ActionController::Live

        def create
          return unless require_feature!(:conversation)

          set_sse_headers

          service = Ai::ChatService.new(
            messages:  chat_params[:messages].map(&:to_h),
            topic_id:  chat_params[:topic_id],
            interests: @current_user.interests,
            wrap_up:   chat_params[:wrap_up] == true,
            mode:      chat_params[:mode] || "practice"
          )

          service.stream do |delta|
            response.stream.write("data: #{JSON.generate({ delta: delta })}\n\n")
          end

          response.stream.write("data: [DONE]\n\n")
        rescue ActionController::Live::ClientDisconnected
          # 클라이언트가 연결을 끊음 — 정상적인 종료로 처리
        rescue => e
          Rails.logger.error("ChatController error: #{e.class}: #{e.message}")
          response.stream.write("data: #{JSON.generate({ error: 'stream_error' })}\n\n") rescue nil
        ensure
          response.stream.close
        end

        private

        def set_sse_headers
          response.headers["Content-Type"]      = "text/event-stream"
          response.headers["Cache-Control"]     = "no-cache"
          response.headers["X-Accel-Buffering"] = "no"
        end

        def chat_params
          params.permit(:topic_id, :wrap_up, :mode, messages: [:role, :content])
        end
      end
    end
  end
end
