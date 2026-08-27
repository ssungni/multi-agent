# 사용자가 보유한 멤버십(기간, 부여 방식, 활성 상태)을 관리하는 모델
class UserMembership < ApplicationRecord
  belongs_to :user
  belongs_to :membership_plan
  belongs_to :payment, optional: true

  enum :granted_by, {
    admin:   "admin",
    payment: "payment"
  }, validate: true

  # 활성 멤버십: soft delete되지 않았고 만료되지 않은 것
  scope :active, -> {
    where(deleted_at: nil)
      .where("expires_at > ?", Time.current)
  }

  scope :expired, -> {
    where(deleted_at: nil)
      .where("expires_at <= ?", Time.current)
  }

  validates :starts_at,  presence: true
  validates :expires_at, presence: true
  validates :granted_by, presence: true

  validate :expires_at_after_starts_at
  validate :payment_required_when_granted_by_payment
  validate :no_duplicate_active_membership, on: :create

  # soft delete되지 않았고 만료 시점도 지나지 않은 경우에만 활성으로 판단
  def active?
    deleted_at.nil? && expires_at > Time.current
  end

  def allows?(feature)
    membership_plan.public_send(:"feature_#{feature}")
  end

  # 실제 row를 삭제하지 않고 deleted_at만 기록해 이력을 보존
  def soft_delete!
    update!(deleted_at: Time.current)
  end

  # 만료까지 남은 일수(올림 처리), 비활성 상태면 0
  def days_remaining
    return 0 unless active?

    ((expires_at - Time.current) / 1.day).ceil
  end

  private

  def expires_at_after_starts_at
    return unless starts_at && expires_at
    return if expires_at > starts_at

    errors.add(:expires_at, "starts_at보다 이후여야 합니다")
  end

  # granted_by가 payment인 경우에만 결제 연결을 필수로 요구 (admin이 부여한 경우는 결제 불필요)
  def payment_required_when_granted_by_payment
    return unless granted_by == "payment"
    return if payment.present?

    errors.add(:payment, "결제 정보가 필요합니다")
  end

  # 한 사용자가 동시에 여러 활성 멤버십을 갖지 못하도록 생성 시점에 차단
  def no_duplicate_active_membership
    return unless user_id
    return unless user.user_memberships.active.exists?

    errors.add(:user, "이미 활성 멤버십이 존재합니다")
  end
end
