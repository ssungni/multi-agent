# User 모델의 인증, 검증, 멤버십 관련 메서드를 검증하는 스펙
require "rails_helper"

RSpec.describe User, type: :model do
  # validate_uniqueness_of가 비교용 레코드를 만들 때 before_save(email.downcase)가
  # nil에 호출되지 않도록 유효한 subject를 지정한다.
  subject { build(:user) }

  # ─── Associations ────────────────────────────────────────────────────────────
  it { is_expected.to have_many(:user_memberships).dependent(:destroy) }
  it { is_expected.to have_many(:payments).dependent(:destroy) }

  # ─── Validations ─────────────────────────────────────────────────────────────
  it { is_expected.to validate_presence_of(:email) }
  it { is_expected.to validate_presence_of(:name) }
  it { is_expected.to validate_length_of(:name).is_at_most(100) }
  it { is_expected.to validate_uniqueness_of(:email).case_insensitive }
  it { is_expected.to validate_presence_of(:phone_number) }
  it { is_expected.to validate_length_of(:phone_number).is_at_most(20) }

  # ─── 비밀번호 (has_secure_password) ──────────────────────────────────────────
  describe "비밀번호" do
    it "생성 시 비밀번호가 없으면 유효하지 않다" do
      user = build(:user, password: nil)
      expect(user).not_to be_valid
      expect(user.errors[:password]).to be_present
    end

    it "비밀번호가 8자 미만이면 유효하지 않다" do
      user = build(:user, password: "short1")
      expect(user).not_to be_valid
      expect(user.errors[:password]).to be_present
    end

    it "올바른 비밀번호로 #authenticate가 true를 반환한다" do
      user = create(:user, password: "password123")
      expect(user.authenticate("password123")).to eq(user)
    end

    it "잘못된 비밀번호로 #authenticate가 false를 반환한다" do
      user = create(:user, password: "password123")
      expect(user.authenticate("wrong-password")).to be false
    end

    it "비밀번호는 평문이 아니라 digest로 저장된다" do
      user = create(:user, password: "password123")
      expect(user.password_digest).not_to eq("password123")
    end
  end

  # ─── 관심사(interests) ────────────────────────────────────────────────────────
  describe "interests" do
    it "기본값은 빈 배열이다" do
      user = create(:user)
      expect(user.interests).to eq([])
    end

    it "Ai::ChatService::TOPICS에 있는 키는 허용한다" do
      user = build(:user, interests: %w[tutor_food tutor_travel])
      expect(user).to be_valid
    end

    it "알 수 없는 값이 섞여 있으면 유효하지 않다" do
      user = build(:user, interests: %w[tutor_food not_a_real_topic])
      expect(user).not_to be_valid
      expect(user.errors[:interests]).to be_present
    end
  end

  describe "email format validation" do
    it "유효한 이메일 주소를 허용한다" do
      user = build(:user, email: "test@example.com")
      expect(user).to be_valid
    end

    it "@가 없는 이메일을 거부한다" do
      user = build(:user, email: "not-an-email")
      expect(user).not_to be_valid
      expect(user.errors[:email]).to be_present
    end

    it "도메인이 없는 이메일을 거부한다" do
      user = build(:user, email: "user@")
      expect(user).not_to be_valid
    end
  end

  # ─── before_save: email 소문자 변환 ──────────────────────────────────────────
  describe "email downcasing" do
    it "저장 전에 이메일을 소문자로 변환한다" do
      user = create(:user, email: "TEST@EXAMPLE.COM")
      expect(user.reload.email).to eq("test@example.com")
    end

    it "혼합 케이스 이메일도 소문자로 변환된다" do
      user = create(:user, email: "User.Name@Example.COM")
      expect(user.reload.email).to eq("user.name@example.com")
    end
  end

  # ─── #active_membership ──────────────────────────────────────────────────────
  describe "#active_membership" do
    let!(:user) { create(:user) }

    context "활성 멤버십이 없는 경우" do
      it "nil을 반환한다" do
        expect(user.active_membership).to be_nil
      end
    end

    context "활성 멤버십이 있는 경우" do
      let!(:membership) { create(:user_membership, :active, user: user) }

      it "활성 멤버십을 반환한다" do
        expect(user.active_membership).to eq(membership)
      end
    end

    context "만료된 멤버십만 있는 경우" do
      before { create(:user_membership, :expired, user: user) }

      it "nil을 반환한다" do
        expect(user.active_membership).to be_nil
      end
    end

    context "여러 멤버십이 있는 경우" do
      let!(:older) { create(:user_membership, :active, user: user, created_at: 2.days.ago) }
      let!(:newer) do
        # 동일 유저의 두 번째 활성 멤버십은 no_duplicate_active_membership에 걸리므로
        # validation을 우회해 데이터 정합성 이슈 상황을 시뮬레이션한다.
        m = build(:user_membership, user: user, starts_at: 1.day.ago, expires_at: 30.days.from_now)
        m.save!(validate: false)
        m
      end

      it "가장 최근에 생성된 멤버십을 반환한다" do
        expect(user.active_membership).to eq(newer)
      end
    end
  end

  # ─── #allows? ────────────────────────────────────────────────────────────────
  describe "#allows?" do
    let(:user) { create(:user) }

    context "활성 멤버십이 없는 경우" do
      it "false를 반환한다" do
        expect(user.allows?(:conversation)).to be false
      end
    end

    context "프리미엄 플랜 멤버십이 있는 경우" do
      let(:premium_plan) { create(:membership_plan, :premium) }

      before { create(:user_membership, :active, user: user, membership_plan: premium_plan) }

      it "conversation을 허용한다" do
        expect(user.allows?(:conversation)).to be true
      end

      it "learning을 허용한다" do
        expect(user.allows?(:learning)).to be true
      end
    end

    context "베이직 플랜 멤버십이 있는 경우" do
      let(:basic_plan) { create(:membership_plan, :basic) }

      before { create(:user_membership, :active, user: user, membership_plan: basic_plan) }

      it "conversation을 허용하지 않는다" do
        expect(user.allows?(:conversation)).to be false
      end

      it "learning을 허용한다" do
        expect(user.allows?(:learning)).to be true
      end
    end
  end
end
