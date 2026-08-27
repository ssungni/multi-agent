# 대화 학습에 사용되는 주제(토픽) 모델
class Topic < ApplicationRecord
  validates :title,      presence: true
  validates :category,   presence: true
  validates :image_url,  presence: true
  validates :english_1,  presence: true
  validates :korean_1,   presence: true
  validates :english_2,  presence: true
  validates :korean_2,   presence: true

  # 관리자가 지정한 노출 순서(position)대로 정렬
  scope :ordered, -> { order(:position, :id) }
end
