# 학습용 주제(토픽) 테이블 생성 (영한 대역 리딩 콘텐츠 포함)
class CreateTopics < ActiveRecord::Migration[7.1]
  def change
    create_table :topics do |t|
      t.string  :title,    null: false
      t.integer :position, null: false, default: 0

      t.timestamps

      # 이미지 + 2단락 영한 대역 리딩 콘텐츠 구조
      t.string :category,  null: false, default: ""
      t.string :image_url, null: false, default: ""
      t.text   :english_1, null: false, default: ""
      t.text   :korean_1,  null: false, default: ""
      t.text   :english_2, null: false, default: ""
      t.text   :korean_2,  null: false, default: ""
    end

    add_index :topics, :position
  end
end
