# Rack 서버 구동을 위한 진입 파일
require_relative "config/environment"

run Rails.application
Rails.application.load_server
