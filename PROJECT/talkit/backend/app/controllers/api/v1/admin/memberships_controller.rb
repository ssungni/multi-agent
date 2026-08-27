module Api
  module V1
    module Admin
      # 관리자가 사용자에게 멤버십을 직접 부여/회수하는 기능
      class MembershipsController < BaseController
        def create
          user = User.find_by(id: create_params[:user_id])
          return render_not_found("user") unless user

          plan = MembershipPlan.active.find_by(id: create_params[:membership_plan_id])
          return render_not_found("membership_plan") unless plan

          starts_at  = parse_starts_at!
          result     = MembershipGrantService.call(
            user:            user,
            membership_plan: plan,
            granted_by:      :admin,
            starts_at:       starts_at
          )

          render json: { membership: serialize(result.membership, replaced: result.replaced?) },
                 status: :created
        rescue ArgumentError => e
          render_error(:unprocessable_entity, "invalid_params", message: e.message)
        rescue MembershipGrantService::PlanInactiveError => e
          render_error(:unprocessable_entity, "plan_inactive", message: e.message)
        end

        def destroy
          membership = UserMembership.find_by(id: params[:id])
          return render_not_found("membership") unless membership

          if membership.deleted_at?
            return render_error(:unprocessable_entity, "membership_already_deleted",
                                message: "이미 삭제된 멤버십입니다.")
          end

          membership.soft_delete!
          render json: { message: "멤버십이 삭제되었습니다." }
        end

        private

        def create_params
          params.permit(:user_id, :membership_plan_id, :starts_at)
        end

        def parse_starts_at!
          return Time.current if create_params[:starts_at].blank?

          parsed = Time.zone.parse(create_params[:starts_at].to_s)
          # Time.zone.parse는 파싱 불가능한 문자열에 대해 예외 대신 nil을 반환하는 경우가 있다.
          raise ArgumentError if parsed.nil?

          parsed
        rescue ArgumentError
          raise ArgumentError, "유효하지 않은 날짜 형식입니다: #{create_params[:starts_at]}"
        end

        def render_not_found(resource)
          render_error(:not_found, "#{resource}_not_found")
        end

        def serialize(membership, replaced: false)
          serializer = MembershipSerializer.new(membership)
          {
            id:             membership.id,
            user_id:        membership.user_id,
            granted_by:     membership.granted_by,
            starts_at:      membership.starts_at,
            expires_at:     membership.expires_at,
            days_remaining: serializer.days_remaining,
            replaced:       replaced,
            plan:           serializer.plan_summary_with_duration
          }
        end
      end
    end
  end
end
