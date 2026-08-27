module Api
  module V1
    # API v1 전체 컨트롤러의 공통 베이스: 인증, 권한 체크, 에러 렌더링을 일괄 처리
    class ApplicationController < ::ApplicationController
      include Api::V1::ErrorRenderable

      before_action :authenticate_user!

      rescue_from ActiveRecord::RecordNotFound do
        render_error(:not_found, "not_found")
      end

      private

      # X-User-Id 헤더 기반의 간이 인증. 사용자를 찾지 못하면 401로 응답하고 액션 실행을 막는다
      def authenticate_user!
        user_id = request.headers["X-User-Id"].to_s
        @current_user = User.find_by(id: user_id)

        render_error(:unauthorized, "unauthorized") unless @current_user
      end

      # Returns false and renders 403 if the current user lacks the feature.
      # Controllers must `return unless require_feature!(...)` to halt execution.
      def require_feature!(feature)
        membership = @current_user.user_memberships.active.first
        return true if membership&.allows?(feature)

        render_error(:forbidden, "feature_not_allowed", feature: feature)
        false
      end
    end
  end
end
