# UserMembership을 API 응답용 형태로 가공해 여러 컨트롤러에서 재사용하는 직렬화 클래스
class MembershipSerializer
  def initialize(membership)
    @membership = membership
  end

  def plan_name
    @membership.membership_plan.name
  end

  def plan_summary
    plan = @membership.membership_plan
    { id: plan.id, name: plan.name, features: plan.features }
  end

  def plan_summary_with_duration
    plan_summary.merge(duration_days: @membership.membership_plan.duration_days)
  end

  def days_remaining
    @membership.days_remaining
  end
end
