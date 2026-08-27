# RoleplayScenario 모델의 검증과 정렬 스코프를 검증하는 스펙
require "rails_helper"

RSpec.describe RoleplayScenario, type: :model do
  subject { build(:roleplay_scenario) }

  it { is_expected.to validate_presence_of(:series_title) }
  it { is_expected.to validate_presence_of(:title) }
  it { is_expected.to validate_presence_of(:level) }
  it { is_expected.to validate_presence_of(:description) }
  it { is_expected.to validate_presence_of(:topic_id) }
  it { is_expected.to validate_inclusion_of(:level).in_array(RoleplayScenario::LEVELS) }

  describe ".ordered" do
    it "series_title, position 순으로 정렬한다" do
      b2 = create(:roleplay_scenario, series_title: "B", position: 2)
      b1 = create(:roleplay_scenario, series_title: "B", position: 1)
      a1 = create(:roleplay_scenario, series_title: "A", position: 1)

      expect(RoleplayScenario.ordered.to_a).to eq([a1, b1, b2])
    end
  end
end
