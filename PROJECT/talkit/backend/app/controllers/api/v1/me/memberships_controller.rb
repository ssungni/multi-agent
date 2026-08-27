module Api
  module V1
    module Me
      class MembershipsController < Api::V1::ApplicationController
        def show
          membership = @current_user
                         .user_memberships
                         .active
                         .includes(:membership_plan)
                         .order(created_at: :desc)
                         .first

          if membership
            render json: { membership: serialize(membership) }
          else
            # 활성 멤버십은 없지만, 과거에 만료된 멤버십이 있었다면 그 정보도 같이 내려줘서
            # 프론트가 "원래 없었음"과 "만료됨"을 구분해 보여줄 수 있게 한다.
            expired = @current_user
                        .user_memberships
                        .expired
                        .includes(:membership_plan)
                        .order(expires_at: :desc)
                        .first
            render_error(:not_found, "no_active_membership",
                         expired_membership: expired ? serialize(expired) : nil)
          end
        end

        private

        def serialize(membership)
          serializer = MembershipSerializer.new(membership)
          {
            id:             membership.id,
            plan:           serializer.plan_summary,
            starts_at:      membership.starts_at,
            expires_at:     membership.expires_at,
            days_remaining: serializer.days_remaining
          }
        end
      end
    end
  end
end
