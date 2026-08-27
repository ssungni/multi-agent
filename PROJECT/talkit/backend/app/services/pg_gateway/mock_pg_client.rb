module PgGateway
  # 실제 PG사 게이트웨이가 구현해야 할 인터페이스
  module GatewayInterface
    # @param amount_cents [Integer]
    # @param card_token   [String]
    # @return [Hash] { success: Boolean, transaction_id?: String, error?: String }
    def charge(amount_cents:, card_token:)
      raise NotImplementedError, "#{self.class}#charge is not implemented"
    end
  end

  # 테스트/개발용 Mock PG 클라이언트.
  # card_token에 따라 다양한 실패 시나리오를 시뮬레이션한다.
  class MockPgClient
    include GatewayInterface

    FAIL_TOKEN = "tok_mock_fail"

    # token → 실패 응답 매핑. 실제 PG사 에러 코드를 모방한다.
    FAILURE_SCENARIOS = {
      "tok_mock_fail"          => "insufficient_funds",
      "tok_mock_expired"       => "expired_card",
      "tok_mock_stolen"        => "card_declined",
      "tok_mock_limit_reached" => "limit_reached"
    }.freeze

    # card_token이 FAILURE_SCENARIOS에 등록된 테스트용 토큰이면 실패 응답을, 아니면 성공 응답을 반환
    def charge(amount_cents:, card_token:)
      if (error_code = FAILURE_SCENARIOS[card_token])
        failure_response(error_code)
      else
        success_response(amount_cents)
      end
    end

    private

    def success_response(amount_cents)
      {
        success:        true,
        transaction_id: "mock_#{SecureRandom.hex(8)}",
        amount_cents:   amount_cents,
        charged_at:     Time.current.iso8601
      }
    end

    def failure_response(error_code)
      {
        success: false,
        error:   error_code
      }
    end
  end
end
