# Rails 환경에서 RSpec을 실행하기 위한 전역 설정 (트랜잭션 픽스처, FactoryBot, Shoulda Matchers 등)
require "spec_helper"

ENV["RAILS_ENV"] ||= "test"
require_relative "../config/environment"

abort("The Rails environment is running in production mode!") if Rails.env.production?

require "rspec/rails"

Dir[Rails.root.join("spec/support/**/*.rb")].sort.each { |f| require f }

begin
  ActiveRecord::Migration.maintain_test_schema!
rescue ActiveRecord::PendingMigrationError => e
  abort e.to_s.strip
end

RSpec.configure do |config|
  config.fixture_paths = [Rails.root.join("spec/fixtures")]
  config.use_transactional_fixtures = true
  config.infer_spec_type_from_file_location!
  config.filter_rails_from_backtrace!

  config.include FactoryBot::Syntax::Methods
  config.include ActiveSupport::Testing::TimeHelpers

  # Rack::Attack의 throttle 카운터는 테스트 간에도 유지되므로, 같은 IP/유저로
  # 반복 호출하는 스펙(예: 로그인)이 서로의 카운트에 영향을 주지 않도록 초기화한다.
  config.before { Rack::Attack.cache.store.clear }
end

Shoulda::Matchers.configure do |config|
  config.integrate do |with|
    with.test_framework :rspec
    with.library :rails
  end
end
