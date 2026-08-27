# 테스트 환경 설정 — 캐싱/리로딩을 끄고 예외를 그대로 노출해 spec 실패 원인을 명확히 함
require "active_support/core_ext/integer/time"

Rails.application.configure do
  config.enable_reloading = false
  config.eager_load = ENV["CI"].present?

  config.consider_all_requests_local       = true
  config.action_controller.perform_caching = false

  config.active_support.deprecation = :stderr

  # 테스트에서는 예외를 그대로 노출해 request spec이 실패 원인을 정확히 보도록 한다.
  config.action_dispatch.show_exceptions = :none

  config.active_record.maintain_test_schema = true

  config.log_level = :warn
end
