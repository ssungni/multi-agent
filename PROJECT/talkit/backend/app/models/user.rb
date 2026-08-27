# 회원 정보, 인증, 관심 주제(interests) 검증을 담당하는 사용자 모델
class User < ApplicationRecord
  has_secure_password

  has_many :user_memberships, dependent: :destroy
  has_many :payments,         dependent: :destroy

  validates :email,
            presence: true,
            uniqueness: { case_sensitive: false },
            format: { with: URI::MailTo::EMAIL_REGEXP }
  validates :name, presence: true, length: { maximum: 100 }
  validates :phone_number, presence: true, length: { maximum: 20 }
  validates :password, length: { minimum: 8 }, allow_nil: true
  validate :interests_must_be_known_topics

  before_save { self.email = email.downcase }

  # 현재 유효한(만료되지 않은) 멤버십을 최신순으로 조회
  def active_membership
    user_memberships.active.order(created_at: :desc).first
  end

  # 활성 멤버십이 해당 기능 권한을 포함하는지 확인
  def allows?(feature)
    active_membership&.allows?(feature) || false
  end

  # API 응답용으로 노출 가능한 필드만 추려서 반환
  def as_api_json
    { id: id, email: email, name: name, phone_number: phone_number }
  end

  private

  # interests에는 ChatService가 지원하는 주제만 허용 (지원하지 않는 주제 선택 방지)
  def interests_must_be_known_topics
    unknown = interests.to_a - Ai::ChatService::TOPICS.keys
    return if unknown.empty?

    errors.add(:interests, "포함된 값 중 알 수 없는 주제가 있습니다: #{unknown.join(', ')}")
  end
end
