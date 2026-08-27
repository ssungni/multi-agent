module Api
  module V1
    # 컨트롤러 전반에서 동일한 형태({ error: ... })의 에러 JSON을 렌더링하기 위한 공통 모듈
    module ErrorRenderable
      extend ActiveSupport::Concern

      private

      def render_error(status, error, **extras)
        render json: { error: error }.merge(extras), status: status
      end
    end
  end
end
