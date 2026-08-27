# 사용자 테이블 생성 (이메일/비밀번호 인증, 관심 주제 배열 컬럼 포함)
class CreateUsers < ActiveRecord::Migration[7.1]
  def change
    create_table :users do |t|
      t.string :email, null: false
      t.string :name,  null: false

      t.timestamps

      t.string :phone_number
      t.string :password_digest, null: false, default: ""
      t.string :interests, array: true, null: false, default: []
    end

    add_index :users, :email, unique: true
  end
end
