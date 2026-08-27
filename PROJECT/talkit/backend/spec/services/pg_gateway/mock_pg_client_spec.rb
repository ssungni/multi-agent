# MockPgClient의 카드 토큰별 성공/실패 시나리오 시뮬레이션을 검증하는 스펙
require "rails_helper"

RSpec.describe PgGateway::MockPgClient do
  subject(:client) { described_class.new }

  describe "#charge" do
    context "with a valid card token" do
      let(:result) { client.charge(amount_cents: 219_000, card_token: "tok_valid") }

      it "returns success: true" do
        expect(result[:success]).to be true
      end

      it "returns a transaction_id with mock_ prefix" do
        expect(result[:transaction_id]).to match(/\Amock_[a-f0-9]{16}\z/)
      end

      it "returns the charged amount_cents" do
        expect(result[:amount_cents]).to eq(219_000)
      end

      it "returns charged_at as ISO8601 string" do
        expect(result[:charged_at]).to match(/\A\d{4}-\d{2}-\d{2}T/)
      end

      it "generates unique transaction_ids on repeated calls" do
        txn1 = client.charge(amount_cents: 100, card_token: "tok_a")[:transaction_id]
        txn2 = client.charge(amount_cents: 100, card_token: "tok_b")[:transaction_id]
        expect(txn1).not_to eq(txn2)
      end
    end

    context "with FAIL_TOKEN (insufficient_funds)" do
      let(:result) do
        client.charge(amount_cents: 219_000, card_token: PgGateway::MockPgClient::FAIL_TOKEN)
      end

      it "returns success: false" do
        expect(result[:success]).to be false
      end

      it "returns insufficient_funds error" do
        expect(result[:error]).to eq("insufficient_funds")
      end

      it "does not include transaction_id" do
        expect(result).not_to have_key(:transaction_id)
      end
    end

    context "with tok_mock_expired (expired_card)" do
      let(:result) { client.charge(amount_cents: 100, card_token: "tok_mock_expired") }

      it "returns success: false with expired_card error" do
        expect(result[:success]).to be false
        expect(result[:error]).to eq("expired_card")
      end
    end

    context "with tok_mock_stolen (card_declined)" do
      let(:result) { client.charge(amount_cents: 100, card_token: "tok_mock_stolen") }

      it "returns success: false with card_declined error" do
        expect(result[:success]).to be false
        expect(result[:error]).to eq("card_declined")
      end
    end

    context "with tok_mock_limit_reached" do
      let(:result) { client.charge(amount_cents: 100, card_token: "tok_mock_limit_reached") }

      it "returns success: false with limit_reached error" do
        expect(result[:success]).to be false
        expect(result[:error]).to eq("limit_reached")
      end
    end

    it "implements GatewayInterface" do
      expect(client).to be_a(PgGateway::GatewayInterface)
    end
  end
end
