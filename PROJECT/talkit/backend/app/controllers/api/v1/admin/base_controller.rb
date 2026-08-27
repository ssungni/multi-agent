module Api
  module V1
    module Admin
      # 관리자 API 공통 베이스. 일반 사용자 인증과 별도로 관리자 토큰 기반 인증을 적용
      class BaseController < ::ApplicationController
        include Api::V1::ErrorRenderable

        before_action :authenticate_admin!

        private

        # X-Admin-Token 헤더를 고정된 관리자 토큰과 안전하게(타이밍 공격 방지) 비교
        def authenticate_admin!
          token    = request.headers["X-Admin-Token"].to_s
          expected = ENV.fetch("ADMIN_API_TOKEN", "secret")

          return if token.present? && ActiveSupport::SecurityUtils.secure_compare(token, expected)

          render_error(:unauthorized, "unauthorized")
        end
      end
    end
  end
end
