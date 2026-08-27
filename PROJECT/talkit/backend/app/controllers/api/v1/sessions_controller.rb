module Api
  module V1
    # 이메일 + 비밀번호 로그인. 이메일 존재 여부를 노출하지 않기 위해
    # "이메일 없음"과 "비밀번호 불일치"를 모두 동일한 invalid_credentials로 응답한다.
    class SessionsController < ApplicationController
      skip_before_action :authenticate_user!

      def create
        email = params[:email].to_s.strip

        unless email.match?(URI::MailTo::EMAIL_REGEXP)
          return render_error(:unprocessable_entity, "invalid_email_format",
                               message: "올바른 이메일 형식이 아닙니다: #{email}")
        end

        user = User.find_by(email: email.downcase)

        if user&.authenticate(params[:password].to_s)
          render json: { user: user.as_api_json }, status: :ok
        else
          render_error(:unauthorized, "invalid_credentials")
        end
      end
    end
  end
end
