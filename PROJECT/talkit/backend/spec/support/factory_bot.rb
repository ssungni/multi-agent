# 스펙에서 FactoryBot의 create/build 메서드를 클래스 접두사 없이 바로 쓸 수 있게 설정
RSpec.configure do |config|
  config.include FactoryBot::Syntax::Methods

  # factory_bot_rails gem이 Railtie를 통해 부팅 시 자동으로 정의를 로드하므로
  # FactoryBot.find_definitions를 여기서 다시 호출하면 중복 등록 에러가 발생한다.
end
