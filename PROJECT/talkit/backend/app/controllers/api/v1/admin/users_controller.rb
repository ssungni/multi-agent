module Api
  module V1
    module Admin
      # 관리자용 사용자 목록 조회 (페이지네이션 + 멤버십 현황 포함)
      class UsersController < BaseController
        def index
          users = User.includes(user_memberships: :membership_plan)
                      .order(:created_at)
                      .page(params[:page])
                      .per(20)

          render json: {
            users: users.map { |u| serialize_user(u) },
            meta:  {
              total:    users.total_count,
              page:     users.current_page,
              per_page: 20
            }
          }
        end

        private

        def serialize_user(user)
          # 이미 로드된 컬렉션에서 Ruby 레벨로 필터/탐색하여 N+1을 방지한다.
          memberships = user.user_memberships.to_a
          active      = memberships.find(&:active?)
          # 활성 멤버십이 없을 때만 "가장 최근에 만료된" 멤버십을 찾아 같이 보여준다
          # ("한 번도 결제 안 함"과 "만료됨"을 화면에서 구분할 수 있게).
          expired = active.nil? ? memberships
                                     .select { |m| m.deleted_at.nil? && m.expires_at <= Time.current }
                                     .max_by(&:expires_at) : nil

          {
            id:                 user.id,
            email:              user.email,
            name:               user.name,
            active_membership:  active ? serialize_membership(active) : nil,
            expired_membership: expired ? serialize_membership(expired) : nil
          }
        end

        def serialize_membership(membership)
          {
            id:         membership.id,
            plan_name:  MembershipSerializer.new(membership).plan_name,
            expires_at: membership.expires_at
          }
        end
      end
    end
  end
end
