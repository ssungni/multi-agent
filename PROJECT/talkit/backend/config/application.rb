# Rails 애플리케이션 전역 설정 (API 모드, 타임존, 미들웨어 등)
require_relative "boot"

require "rails"
require "active_model/railtie"
require "active_record/railtie"
require "action_controller/railtie"

Bundler.require(*Rails.groups)

module Talkit
  class Application < Rails::Application
    config.load_defaults 7.1

    # API 전용 모드 — 세션/쿠키/플래시 등 브라우저 전용 미들웨어를 제외한다.
    # 인증은 X-User-Id / X-Admin-Token 헤더로 처리하므로 세션이 불필요하다.
    config.api_only = true

    # 유저별 STT/Chat/TTS 요청 횟수 제한 (config/initializers/rack_attack.rb)
    config.middleware.use Rack::Attack

    config.time_zone = "Seoul"
    config.active_record.default_timezone = :utc
  end
end
