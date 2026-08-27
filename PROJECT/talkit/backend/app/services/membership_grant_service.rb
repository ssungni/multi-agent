# 사용자에게 멤버십을 부여하는 서비스. 결제 완료 시점과 관리자 수동 부여 양쪽에서 공통으로 사용
class MembershipGrantService
  class PlanInactiveError < StandardError; end

  # call이 반환하는 값 객체.
  # membership        — 새로 생성된 UserMembership
  # previous_membership — 교체 전 비활성화된 기존 멤버십 (없으면 nil)
  Result = Struct.new(:membership, :previous_membership, keyword_init: true) do
    def replaced?
      previous_membership.present?
    end
  end

  def self.call(**kwargs)
    new(**kwargs).call
  end

  def initialize(user:, membership_plan:, granted_by:,
                 payment: nil, granted_by_admin_id: nil, starts_at: nil)
    @user                = user
    @membership_plan     = membership_plan
    @granted_by          = granted_by
    @payment             = payment
    @granted_by_admin_id = granted_by_admin_id
    @starts_at           = starts_at || Time.current
  end

  # @return [MembershipGrantService::Result]
  def call
    raise PlanInactiveError, "비활성 플랜은 부여할 수 없습니다" unless @membership_plan.active?

    ActiveRecord::Base.transaction do
      previous   = deactivate_existing_memberships!
      membership = create_membership!
      Result.new(membership: membership, previous_membership: previous)
    end
  end

  private

  # 기존 활성 멤버십을 soft delete하고 첫 번째 항목을 반환한다.
  # 정상적으로는 0~1개이지만, 데이터 정합성 문제로 다수일 경우도 처리한다.
  def deactivate_existing_memberships!
    existing = @user.user_memberships.active.to_a
    existing.each(&:soft_delete!)
    existing.first
  end

  # 새 멤버십을 생성하고 플랜의 기간에 따라 만료일을 계산해서 저장
  def create_membership!
    @user.user_memberships.create!(
      membership_plan:     @membership_plan,
      payment:             @payment,
      granted_by:          @granted_by,
      granted_by_admin_id: @granted_by_admin_id,
      starts_at:           @starts_at,
      expires_at:          @membership_plan.expires_at_from(@starts_at)
    )
  end
end
