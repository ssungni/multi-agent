# 개발 환경 설정 — 코드 자동 리로딩, 상세 로그/에러 노출을 활성화
require "active_support/core_ext/integer/time"

Rails.application.configure do
  config.enable_reloading = true
  config.eager_load = false
  config.consider_all_requests_local = true
  config.server_timing = true

  config.action_controller.perform_caching = false

  config.active_support.deprecation = :log

  config.active_record.migration_error = :page_load
  config.active_record.verbose_query_logs = true

  config.log_level = :debug

  # Vite 프록시가 Docker 서비스명(backend:3000)을 Host 헤더로 보내므로 허용 목록에 추가
  config.hosts << "backend"
end
