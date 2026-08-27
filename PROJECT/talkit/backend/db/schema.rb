# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[7.1].define(version: 2026_06_22_000002) do
  # These are extensions that must be enabled in order to support this database
  enable_extension "plpgsql"

  create_table "membership_plans", force: :cascade do |t|
    t.string "name", null: false
    t.boolean "feature_learning", default: false, null: false
    t.boolean "feature_conversation", default: false, null: false
    t.boolean "feature_analysis", default: false, null: false
    t.integer "duration_days", null: false
    t.integer "price_cents", null: false
    t.string "currency", default: "KRW", null: false
    t.boolean "active", default: true, null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["active"], name: "index_membership_plans_on_active"
    t.index ["name"], name: "index_membership_plans_on_name", unique: true
  end

  create_table "payments", force: :cascade do |t|
    t.bigint "user_id", null: false
    t.bigint "membership_plan_id", null: false
    t.integer "amount_cents", null: false
    t.string "currency", default: "KRW", null: false
    t.string "status", default: "pending", null: false
    t.string "pg_transaction_id"
    t.jsonb "pg_response"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["membership_plan_id"], name: "index_payments_on_membership_plan_id"
    t.index ["pg_transaction_id"], name: "idx_payments_on_pg_transaction_id_not_null", unique: true, where: "(pg_transaction_id IS NOT NULL)"
    t.index ["status"], name: "index_payments_on_status"
    t.index ["user_id", "created_at"], name: "idx_payments_on_user_id_created_at"
    t.index ["user_id"], name: "index_payments_on_user_id"
  end

  create_table "roleplay_scenarios", force: :cascade do |t|
    t.string "series_title", null: false
    t.string "title", null: false
    t.string "level", null: false
    t.text "description", null: false
    t.integer "position", default: 0, null: false
    t.string "topic_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["series_title", "position"], name: "index_roleplay_scenarios_on_series_title_and_position"
  end

  create_table "topics", force: :cascade do |t|
    t.string "title", null: false
    t.integer "position", default: 0, null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.string "category", default: "", null: false
    t.string "image_url", default: "", null: false
    t.text "english_1", default: "", null: false
    t.text "korean_1", default: "", null: false
    t.text "english_2", default: "", null: false
    t.text "korean_2", default: "", null: false
    t.index ["position"], name: "index_topics_on_position"
  end

  create_table "user_memberships", force: :cascade do |t|
    t.bigint "user_id", null: false
    t.bigint "membership_plan_id", null: false
    t.bigint "payment_id"
    t.string "granted_by", null: false
    t.bigint "granted_by_admin_id"
    t.datetime "starts_at", null: false
    t.datetime "expires_at", null: false
    t.datetime "deleted_at"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["expires_at"], name: "index_user_memberships_on_expires_at"
    t.index ["membership_plan_id"], name: "index_user_memberships_on_membership_plan_id"
    t.index ["payment_id"], name: "index_user_memberships_on_payment_id"
    t.index ["user_id", "deleted_at", "expires_at"], name: "idx_user_memberships_on_user_active"
    t.index ["user_id"], name: "index_user_memberships_on_user_id"
  end

  create_table "users", force: :cascade do |t|
    t.string "email", null: false
    t.string "name", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.string "phone_number"
    t.string "password_digest", default: "", null: false
    t.string "interests", default: [], null: false, array: true
    t.index ["email"], name: "index_users_on_email", unique: true
  end

  add_foreign_key "payments", "membership_plans"
  add_foreign_key "payments", "users"
  add_foreign_key "user_memberships", "membership_plans"
  add_foreign_key "user_memberships", "payments"
  add_foreign_key "user_memberships", "users"
end
