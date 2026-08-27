# 멤버십 구매 결제 내역과 상태(대기/완료/실패)를 관리하는 모델
class Payment < ApplicationRecord
  belongs_to :user
  belongs_to :membership_plan
  has_one    :user_membership

  SUPPORTED_CURRENCIES = %w[KRW USD JPY].freeze

  enum :status, {
    pending:   "pending",
    completed: "completed",
    failed:    "failed"
  }, validate: true

  validates :amount_cents,
            presence: true,
            numericality: { only_integer: true, greater_than: 0 }
  validates :currency,
            presence: true,
            inclusion: { in: SUPPORTED_CURRENCIES }
  validates :pg_transaction_id, uniqueness: true, allow_nil: true

  validate :amount_matches_plan_price, on: :create

  private

  # 클라이언트가 보낸 결제 금액이 실제 플랜 가격과 다르게 조작되는 것을 방지
  def amount_matches_plan_price
    return unless membership_plan && amount_cents
    return if amount_cents == membership_plan.price_cents

    errors.add(:amount_cents, "플랜 가격(#{membership_plan.price_cents})과 일치하지 않습니다")
  end
end
