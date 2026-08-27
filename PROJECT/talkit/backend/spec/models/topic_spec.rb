# Topic 모델의 검증과 정렬 스코프를 검증하는 스펙
require "rails_helper"

RSpec.describe Topic, type: :model do
  subject { build(:topic) }

  it { is_expected.to validate_presence_of(:title) }
  it { is_expected.to validate_presence_of(:category) }
  it { is_expected.to validate_presence_of(:image_url) }
  it { is_expected.to validate_presence_of(:english_1) }
  it { is_expected.to validate_presence_of(:korean_1) }
  it { is_expected.to validate_presence_of(:english_2) }
  it { is_expected.to validate_presence_of(:korean_2) }

  describe ".ordered" do
    it "position 오름차순으로 정렬한다" do
      second = create(:topic, position: 2)
      first  = create(:topic, position: 1)

      expect(Topic.ordered.to_a).to eq([first, second])
    end
  end
end
