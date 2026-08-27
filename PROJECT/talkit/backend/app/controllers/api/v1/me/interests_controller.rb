module Api
  module V1
    module Me
      # 로그인한 사용자의 관심 주제(interests) 조회 및 수정
      class InterestsController < Api::V1::ApplicationController
        def show
          render json: { interests: @current_user.interests }
        end

        def update
          if @current_user.update(interests: interests_param)
            render json: { interests: @current_user.interests }
          else
            render_error(:unprocessable_entity, "invalid_params",
                         message: @current_user.errors.full_messages.join(", "))
          end
        end

        private

        def interests_param
          params.permit(interests: [])[:interests] || []
        end
      end
    end
  end
end
