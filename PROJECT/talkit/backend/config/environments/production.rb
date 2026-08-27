# 운영 환경 설정 — eager loading과 캐싱을 활성화해 성능을 최적화
require "active_support/core_ext/integer/time"

Rails.application.configure do
  config.enable_reloading = false
  config.eager_load = true

  config.consider_all_requests_local = false

  config.active_support.deprecation = :notify

  config.log_tags  = [:request_id]
  config.log_level = ENV.fetch("RAILS_LOG_LEVEL", "info")

  config.action_controller.perform_caching = true

  config.active_record.dump_schema_after_migration = false
end
