# AI 호출(chat/stt/tts)은 비용이 발생하므로 사용자별로 분당 호출 횟수를 제한
Rack::Attack.throttle("conversations/chat", limit: 10, period: 60.seconds) do |req|
  req.env["HTTP_X_USER_ID"] if req.post? && req.path.end_with?("/conversations/chat")
end

Rack::Attack.throttle("conversations/stt", limit: 10, period: 60.seconds) do |req|
  req.env["HTTP_X_USER_ID"] if req.post? && req.path.end_with?("/conversations/stt")
end

Rack::Attack.throttle("conversations/tts", limit: 10, period: 60.seconds) do |req|
  req.env["HTTP_X_USER_ID"] if req.post? && req.path.end_with?("/conversations/tts")
end

# 비밀번호 도입에 따른 무차별 대입(brute-force) 방어 — IP 기준
Rack::Attack.throttle("sessions/login", limit: 10, period: 60.seconds) do |req|
  req.ip if req.post? && req.path.end_with?("/sessions")
end

Rack::Attack.throttled_responder = lambda do |request|
  # rack-attack 6.x부터 responder는 raw env Hash가 아니라 Request 객체를 받는다.
  period = request.env["rack.attack.match_data"]&.dig(:period) || 60
  [
    429,
    { "Content-Type" => "application/json", "Retry-After" => period.to_s },
    [JSON.generate({ error: "rate_limit_exceeded", retry_after: period })]
  ]
end

