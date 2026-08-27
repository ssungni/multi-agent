# Bundler 환경과 부팅 캐시(bootsnap)를 초기화하는 진입 스크립트
ENV["BUNDLE_GEMFILE"] ||= File.expand_path("../Gemfile", __dir__)

require "bootsnap/setup" # 부팅 속도 향상을 위한 캐싱
