# 관리자용 멤버십 부여(POST)/삭제(DELETE) API의 인증, 검증, 교체 로직을 검증하는 요청 스펙
require "rails_helper"

RSpec.describe "Admin Memberships API", type: :request do
  let(:admin_headers)   { { "X-Admin-Token" => "secret", "Content-Type" => "application/json" } }
  let(:no_auth_headers) { { "Content-Type" => "application/json" } }
  let(:user)            { create(:user) }
  let(:plan)            { create(:membership_plan, :premium) }

  def json
    JSON.parse(response.body)
  end

  # ─────────────────────────────────────────────
  # POST /api/v1/admin/memberships
  # ─────────────────────────────────────────────
  describe "POST /api/v1/admin/memberships" do
    let(:valid_params) { { user_id: user.id, membership_plan_id: plan.id } }

    def post_admin_membership(params = valid_params, headers = admin_headers)
      post "/api/v1/admin/memberships",
           params: params.to_json,
           headers: headers
    end

    # ──── 성공 케이스 ────

    context "유효한 파라미터" do
      it "201 Created를 반환한다" do
        post_admin_membership
        expect(response).to have_http_status(:created)
      end

      it "UserMembership이 1건 생성된다" do
        expect { post_admin_membership }.to change(UserMembership, :count).by(1)
      end

      it "granted_by가 admin이다" do
        post_admin_membership
        expect(UserMembership.last.granted_by).to eq("admin")
      end

      it "응답에 멤버십 id, user_id, granted_by가 포함된다" do
        post_admin_membership
        expect(json["membership"]).to include(
          "user_id"    => user.id,
          "granted_by" => "admin"
        )
      end

      it "응답에 플랜 정보가 포함된다" do
        post_admin_membership
        expect(json["membership"]["plan"]).to include(
          "name"          => plan.name,
          "duration_days" => plan.duration_days
        )
        expect(json["membership"]["plan"]["features"]).to contain_exactly("learning", "conversation", "analysis")
      end

      it "응답에 expires_at이 존재한다" do
        post_admin_membership
        expect(json["membership"]["expires_at"]).to be_present
      end

      it "응답에 days_remaining이 양수이다" do
        post_admin_membership
        expect(json["membership"]["days_remaining"]).to be_positive
      end

      it "replaced가 false이다 (기존 멤버십 없음)" do
        post_admin_membership
        expect(json["membership"]["replaced"]).to be false
      end
    end

    # ──── 만료일 계산 ────

    describe "만료일 계산" do
      context "starts_at 미지정" do
        it "현재 시각 기준으로 plan.duration_days 후에 만료된다" do
          travel_to(Time.zone.parse("2026-01-01 00:00:00")) do
            post_admin_membership
            expected = Time.zone.parse("2026-01-01") + plan.duration_days.days
            actual   = Time.zone.parse(json["membership"]["expires_at"])
            expect(actual).to be_within(5.seconds).of(expected)
          end
        end
      end

      context "starts_at 지정 (미래 날짜)" do
        let(:future_start) { "2026-09-01T00:00:00Z" }

        it "지정한 starts_at 기준으로 expires_at을 계산한다" do
          post_admin_membership(valid_params.merge(starts_at: future_start))
          expected = Time.zone.parse(future_start) + plan.duration_days.days
          actual   = Time.zone.parse(json["membership"]["expires_at"])
          expect(actual).to be_within(5.seconds).of(expected)
        end

        it "DB의 starts_at이 지정된 값과 일치한다" do
          post_admin_membership(valid_params.merge(starts_at: future_start))
          membership = UserMembership.last
          expect(membership.starts_at).to be_within(1.second).of(Time.zone.parse(future_start))
        end
      end

      context "starts_at 지정 (과거 날짜 — 어드민 소급 부여)" do
        let(:past_start) { "2026-05-01T00:00:00Z" }

        it "과거 날짜도 허용한다" do
          post_admin_membership(valid_params.merge(starts_at: past_start))
          expect(response).to have_http_status(:created)
        end
      end
    end

    # ──── 기존 멤버십 교체 ────

    context "기존 활성 멤버십이 있는 경우" do
      let!(:existing) { create(:user_membership, :active, user: user, membership_plan: plan) }

      it "201을 반환한다" do
        post_admin_membership
        expect(response).to have_http_status(:created)
      end

      it "기존 멤버십이 soft-delete된다" do
        post_admin_membership
        expect(existing.reload.deleted_at).not_to be_nil
      end

      it "활성 멤버십은 1개만 존재한다" do
        post_admin_membership
        expect(user.user_memberships.active.count).to eq(1)
      end

      it "응답의 replaced가 true이다" do
        post_admin_membership
        expect(json["membership"]["replaced"]).to be true
      end

      it "새로 생성된 멤버십이 반환된다" do
        post_admin_membership
        expect(json["membership"]["id"]).not_to eq(existing.id)
      end
    end

    # ──── 인증 실패 ────

    describe "인증 실패" do
      it "X-Admin-Token 헤더 없이 요청하면 401을 반환한다" do
        post_admin_membership(valid_params, no_auth_headers)
        expect(response).to have_http_status(:unauthorized)
        expect(json["error"]).to eq("unauthorized")
      end

      it "잘못된 토큰으로 요청하면 401을 반환한다" do
        post_admin_membership(valid_params, admin_headers.merge("X-Admin-Token" => "wrong"))
        expect(response).to have_http_status(:unauthorized)
      end

      it "인증 실패 시 UserMembership이 생성되지 않는다" do
        expect { post_admin_membership(valid_params, no_auth_headers) }
          .not_to change(UserMembership, :count)
      end
    end

    # ──── 리소스 미존재 ────

    describe "유저 미존재" do
      it "404를 반환한다" do
        post_admin_membership(valid_params.merge(user_id: 999_999))
        expect(response).to have_http_status(:not_found)
        expect(json["error"]).to eq("user_not_found")
      end
    end

    describe "플랜 미존재" do
      it "404를 반환한다" do
        post_admin_membership(valid_params.merge(membership_plan_id: 999_999))
        expect(response).to have_http_status(:not_found)
        expect(json["error"]).to eq("membership_plan_not_found")
      end
    end

    describe "비활성 플랜 (active: false)" do
      let(:inactive_plan) { create(:membership_plan, :premium, :inactive, name: "비활성 프리미엄") }

      it "404를 반환한다 (active 스코프로 필터됨)" do
        post_admin_membership(valid_params.merge(membership_plan_id: inactive_plan.id))
        expect(response).to have_http_status(:not_found)
        expect(json["error"]).to eq("membership_plan_not_found")
      end
    end

    # ──── 입력값 검증 ────

    describe "유효하지 않은 starts_at 형식" do
      it "422 Unprocessable Entity를 반환한다" do
        post_admin_membership(valid_params.merge(starts_at: "not-a-valid-date"))
        expect(response).to have_http_status(:unprocessable_entity)
        expect(json["error"]).to eq("invalid_params")
      end

      it "에러 메시지에 입력값이 포함된다" do
        post_admin_membership(valid_params.merge(starts_at: "not-a-valid-date"))
        expect(json["message"]).to include("not-a-valid-date")
      end
    end
  end

  # ─────────────────────────────────────────────
  # DELETE /api/v1/admin/memberships/:id
  # ─────────────────────────────────────────────
  describe "DELETE /api/v1/admin/memberships/:id" do
    let!(:membership) { create(:user_membership, :active, user: user, membership_plan: plan) }

    def delete_admin_membership(id = membership.id, headers = admin_headers)
      delete "/api/v1/admin/memberships/#{id}", headers: headers
    end

    # ──── 성공 케이스 ────

    context "정상 삭제" do
      it "200 OK를 반환한다" do
        delete_admin_membership
        expect(response).to have_http_status(:ok)
      end

      it "성공 메시지를 반환한다" do
        delete_admin_membership
        expect(json["message"]).to eq("멤버십이 삭제되었습니다.")
      end

      it "deleted_at이 설정된다 (soft delete)" do
        delete_admin_membership
        expect(membership.reload.deleted_at).not_to be_nil
      end

      it "레코드는 DB에 남아 있다 (물리 삭제 아님)" do
        delete_admin_membership
        expect(UserMembership.unscoped.find_by(id: membership.id)).not_to be_nil
      end

      it ".active 스코프에서 제외된다" do
        delete_admin_membership
        expect(UserMembership.active).not_to include(membership)
      end
    end

    # ──── 인증 실패 ────

    describe "인증 실패" do
      it "X-Admin-Token 없이 요청하면 401을 반환한다" do
        delete_admin_membership(membership.id, no_auth_headers)
        expect(response).to have_http_status(:unauthorized)
      end

      it "인증 실패 시 deleted_at이 설정되지 않는다" do
        delete_admin_membership(membership.id, no_auth_headers)
        expect(membership.reload.deleted_at).to be_nil
      end
    end

    # ──── 리소스 미존재 ────

    describe "존재하지 않는 멤버십 id" do
      it "404를 반환한다" do
        delete_admin_membership(999_999)
        expect(response).to have_http_status(:not_found)
        expect(json["error"]).to eq("membership_not_found")
      end
    end

    # ──── 중복 삭제 ────

    describe "이미 삭제된 멤버십" do
      before { membership.soft_delete! }

      it "422 Unprocessable Entity를 반환한다" do
        delete_admin_membership
        expect(response).to have_http_status(:unprocessable_entity)
        expect(json["error"]).to eq("membership_already_deleted")
      end
    end

    # ──── 만료된 멤버십 삭제 (유효한 케이스) ────

    describe "만료된 멤버십 삭제" do
      # 바깥 컨텍스트의 `user`는 이미 활성 멤버십(`membership`)을 보유하고 있어
      # 동일 user로 추가 멤버십을 생성하면 no_duplicate_active_membership에 걸린다.
      # 만료 멤버십 단독 시나리오를 위해 별도 유저를 사용한다.
      let(:other_user) { create(:user) }
      let!(:expired_membership) do
        create(:user_membership, :expired, user: other_user, membership_plan: plan)
      end

      it "200을 반환한다 (만료된 멤버십도 삭제 가능)" do
        delete "/api/v1/admin/memberships/#{expired_membership.id}",
               headers: admin_headers
        expect(response).to have_http_status(:ok)
      end

      it "deleted_at이 설정된다" do
        delete "/api/v1/admin/memberships/#{expired_membership.id}",
               headers: admin_headers
        expect(expired_membership.reload.deleted_at).not_to be_nil
      end
    end
  end
end
