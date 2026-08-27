# 결제 내역 테이블 생성. pg_transaction_id는 PG사 응답이 있을 때만 유니크해야 하므로
# 부분 인덱스(where절)로 NULL 값들끼리는 중복을 허용한다.
class CreatePayments < ActiveRecord::Migration[7.1]
  def change
    create_table :payments do |t|
      t.references :user,            null: false, foreign_key: true
      t.references :membership_plan, null: false, foreign_key: true
      t.integer    :amount_cents,    null: false
      t.string     :currency,        null: false, default: "KRW"
      t.string     :status,          null: false, default: "pending"
      t.string     :pg_transaction_id
      t.jsonb      :pg_response

      t.timestamps
    end

    add_index :payments, :status
    add_index :payments, :pg_transaction_id,
              unique: true,
              where: "pg_transaction_id IS NOT NULL",
              name: "idx_payments_on_pg_transaction_id_not_null"
    add_index :payments, %i[user_id created_at],
              name: "idx_payments_on_user_id_created_at"
  end
end
