# 결제로 구매 가능한 멤버십 요금제(가격, 기간, 기능 권한)를 정의하는 모델
class MembershipPlan < ApplicationRecord
  has_many :user_memberships
  has_many :payments

  SUPPORTED_CURRENCIES = %w[KRW USD JPY].freeze
  FEATURES = %i[learning conversation analysis].freeze

  scope :active, -> { where(active: true) }

  validates :name,
            presence: true,
            uniqueness: true,
            length: { maximum: 100 }
  validates :duration_days,
            presence: true,
            numericality: { only_integer: true, greater_than: 0 }
  validates :price_cents,
            presence: true,
            numericality: { only_integer: true, greater_than_or_equal_to: 0 }
  validates :currency,
            presence: true,
            inclusion: { in: SUPPORTED_CURRENCIES }
  validates :active, inclusion: { in: [true, false] }

  validate :at_least_one_feature_enabled

  # 이 플랜에서 활성화된 기능 목록만 반환
  def features
    FEATURES.select { |f| public_send(:"feature_#{f}") }
  end

  # 시작 시점 기준으로 플랜의 만료 시점을 계산
  def expires_at_from(starts_at)
    starts_at + duration_days.days
  end

  private

  # 아무 기능도 없는 빈 플랜이 생성되는 것을 방지
  def at_least_one_feature_enabled
    return if feature_learning || feature_conversation || feature_analysis

    errors.add(:base, "최소 하나의 기능 권한을 활성화해야 합니다")
  end
end
