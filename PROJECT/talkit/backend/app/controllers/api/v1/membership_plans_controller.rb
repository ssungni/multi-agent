module Api
  module V1
    # 구매 가능한 멤버십 요금제 목록 제공. 가입 전 사용자도 볼 수 있어야 하므로 인증 불필요
    class MembershipPlansController < ApplicationController
      skip_before_action :authenticate_user!

      def index
        plans = MembershipPlan.active.order(:price_cents)
        render json: { plans: plans.map { |p| serialize(p) } }
      end

      private

      def serialize(plan)
        {
          id:            plan.id,
          name:          plan.name,
          features:      plan.features,
          duration_days: plan.duration_days,
          price_cents:   plan.price_cents,
          currency:      plan.currency
        }
      end
    end
  end
end
