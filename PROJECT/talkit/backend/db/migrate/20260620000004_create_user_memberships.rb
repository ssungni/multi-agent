# 사용자별 멤버십 보유 내역 테이블 생성 (활성/만료 조회에 최적화된 인덱스 포함)
class CreateUserMemberships < ActiveRecord::Migration[7.1]
  def change
    create_table :user_memberships do |t|
      t.references :user,            null: false, foreign_key: true
      t.references :membership_plan, null: false, foreign_key: true
      t.references :payment,         null: true,  foreign_key: true
      t.string     :granted_by,      null: false
      t.bigint     :granted_by_admin_id
      t.datetime   :starts_at,       null: false
      t.datetime   :expires_at,      null: false
      t.datetime   :deleted_at

      t.timestamps
    end

    # 활성 멤버십 조회 핵심 인덱스 (매 API 요청마다 사용)
    add_index :user_memberships, %i[user_id deleted_at expires_at],
              name: "idx_user_memberships_on_user_active"

    # 만료 배치 스캔 / 임박 알림용
    add_index :user_memberships, :expires_at

    # membership_plan_id / payment_id 인덱스는 위 t.references(foreign_key: true)가
    # 이미 자동 생성하므로(index: true가 기본값) 별도 add_index가 불필요하다.
  end
end
