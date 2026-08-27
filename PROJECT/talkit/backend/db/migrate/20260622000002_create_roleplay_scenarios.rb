# 롤플레잉 시나리오 테이블 생성 (시리즈/레벨별 분류, topic_id로 AI 프롬프트와 연결)
class CreateRoleplayScenarios < ActiveRecord::Migration[7.1]
  def change
    create_table :roleplay_scenarios do |t|
      t.string  :series_title, null: false
      t.string  :title,        null: false
      t.string  :level,        null: false
      t.text    :description,  null: false
      t.integer :position,     null: false, default: 0
      # Ai::ChatService::TOPICS의 키와 매칭되어 시나리오별 system prompt를 결정한다.
      t.string  :topic_id,     null: false

      t.timestamps
    end

    add_index :roleplay_scenarios, [:series_title, :position]
  end
end
