# 롤플레잉 대화 연습에 사용되는 시나리오 모델
class RoleplayScenario < ApplicationRecord
  LEVELS = %w[Basic Intermediate Advanced].freeze

  validates :series_title, presence: true
  validates :title,        presence: true
  validates :level,        presence: true, inclusion: { in: LEVELS }
  validates :description,  presence: true
  validates :topic_id,     presence: true

  # 시리즈별로 묶고 그 안에서는 지정된 순서(position)대로 정렬
  scope :ordered, -> { order(:series_title, :position, :id) }
end
