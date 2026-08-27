module Api
  module V1
    # 회원가입(사용자 생성) 처리. 가입 전이라 인증된 사용자가 없으므로 인증 체크를 건너뜀
    class UsersController < ApplicationController
      skip_before_action :authenticate_user!

      def create
        user = User.new(user_params)

        if user.save
          render json: { user: user.as_api_json }, status: :created
        else
          render_error(:unprocessable_entity, "invalid_params",
                       message: user.errors.full_messages.join(", "))
        end
      end

      private

      def user_params
        params.permit(:email, :name, :phone_number, :password, :password_confirmation)
      end
    end
  end
end
