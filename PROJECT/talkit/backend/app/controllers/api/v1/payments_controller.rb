module Api
  module V1
    # 멤버십 결제 처리. PG 결제와 멤버십 부여를 PaymentService에 위임하고 결과만 직렬화
    class PaymentsController < ApplicationController
      def create
        plan = MembershipPlan.active.find_by(id: payment_params[:membership_plan_id])
        return render_error(:not_found, "membership_plan_not_found") unless plan

        payment, membership = PaymentService.call(
          user:            @current_user,
          membership_plan: plan,
          card_token:      payment_params[:card_token].to_s
        )

        render json: {
          payment:    serialize_payment(payment),
          membership: serialize_membership(membership)
        }, status: :created
      rescue PaymentService::PaymentFailedError => e
        render_error(:unprocessable_entity, "payment_failed", message: e.message)
      rescue PaymentService::PaymentGrantError
        # PG 청구는 성공했으나 멤버십 생성 실패 — 운영자가 수동 처리해야 함
        render_error(:internal_server_error, "payment_grant_failed",
                     message: "결제는 완료되었으나 멤버십 생성에 실패했습니다. 고객센터에 문의해 주세요.")
      end

      private

      def payment_params
        params.permit(:membership_plan_id, :card_token, :payment_method)
      end

      def serialize_payment(payment)
        {
          id:           payment.id,
          status:       payment.status,
          amount_cents: payment.amount_cents,
          currency:     payment.currency
        }
      end

      def serialize_membership(membership)
        {
          id:         membership.id,
          expires_at: membership.expires_at,
          plan_name:  MembershipSerializer.new(membership).plan_name
        }
      end
    end
  end
end
