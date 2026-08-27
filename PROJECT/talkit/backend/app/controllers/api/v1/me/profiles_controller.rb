module Api
  module V1
    module Me
      # 로그인한 사용자 본인의 프로필 정보 조회
      class ProfilesController < Api::V1::ApplicationController
        def show
          render json: {
            id:           @current_user.id,
            email:        @current_user.email,
            name:         @current_user.name,
            phone_number: @current_user.phone_number
          }
        end
      end
    end
  end
end
