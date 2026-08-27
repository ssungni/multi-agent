# PG 결제 청구와 멤버십 부여를 한 흐름으로 처리하는 서비스
class PaymentService
  # PG 게이트웨이가 결제를 거절한 경우
  class PaymentFailedError < StandardError
    attr_reader :pg_error

    def initialize(pg_error)
      @pg_error = pg_error
      super("결제에 실패했습니다: #{pg_error}")
    end
  end

  # PG 청구는 성공했으나 DB 멤버십 생성에 실패한 경우.
  # 결제 금액은 청구되었으므로 운영자 개입이 필요하다.
  class PaymentGrantError < StandardError; end

  def self.call(**kwargs)
    new(**kwargs).call
  end

  def initialize(user:, membership_plan:, card_token:,
                 gateway: PgGateway::MockPgClient.new)
    @user            = user
    @membership_plan = membership_plan
    @card_token      = card_token
    @gateway         = gateway
  end

  # @return [Array<Payment, UserMembership>]
  def call
    payment = create_pending_payment!
    result  = @gateway.charge(
      amount_cents: @membership_plan.price_cents,
      card_token:   @card_token
    )

    if result[:success]
      membership = complete_and_grant!(payment, result)
      [payment, membership]
    else
      payment.update!(status: :failed, pg_response: result.stringify_keys)
      raise PaymentFailedError.new(result[:error])
    end
  end

  private

  # PG 청구 전 pending 상태의 결제 레코드를 먼저 만들어 결제 시도 자체를 항상 기록
  def create_pending_payment!
    @user.payments.create!(
      membership_plan: @membership_plan,
      amount_cents:    @membership_plan.price_cents,
      currency:        @membership_plan.currency,
      status:          :pending
    )
  end

  # payment 상태 업데이트와 멤버십 생성을 단일 트랜잭션으로 묶는다.
  # MembershipGrantService 내부에도 transaction이 있지만, Rails는 중첩 트랜잭션을
  # savepoint로 처리하므로 외부 트랜잭션이 롤백되면 payment.update!도 함께 롤백된다.
  def complete_and_grant!(payment, result)
    ActiveRecord::Base.transaction do
      payment.update!(
        status:            :completed,
        pg_transaction_id: result[:transaction_id],
        pg_response:       result.stringify_keys
      )

      grant_result = MembershipGrantService.call(
        user:            @user,
        membership_plan: @membership_plan,
        granted_by:      :payment,
        payment:         payment
      )
      grant_result.membership
    end
  rescue ActiveRecord::RecordInvalid, MembershipGrantService::PlanInactiveError => e
    # 트랜잭션이 롤백되어 payment는 :pending 상태로 복원됨.
    # PG에 청구는 완료된 상태이므로 운영자 알림이 필요하다.
    Rails.logger.error(
      "[PaymentService] Charge succeeded but grant failed — manual intervention required. " \
      "User: #{@user.id}, Plan: #{@membership_plan.id}, Error: #{e.class}: #{e.message}"
    )
    raise PaymentGrantError, e.message
  end
end
