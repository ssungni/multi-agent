# 멤버십 요금제 테이블 생성 (기능 권한 플래그, 가격, 기간 정보 포함)
class CreateMembershipPlans < ActiveRecord::Migration[7.1]
  def change
    create_table :membership_plans do |t|
      t.string  :name,                 null: false
      t.boolean :feature_learning,     null: false, default: false
      t.boolean :feature_conversation, null: false, default: false
      t.boolean :feature_analysis,     null: false, default: false
      t.integer :duration_days,        null: false
      t.integer :price_cents,          null: false
      t.string  :currency,             null: false, default: "KRW"
      t.boolean :active,               null: false, default: true

      t.timestamps
    end

    add_index :membership_plans, :name,   unique: true
    add_index :membership_plans, :active
  end
end
