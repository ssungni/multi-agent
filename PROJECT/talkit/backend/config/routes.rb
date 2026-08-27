# API v1 라우트 정의 — 공개 엔드포인트, 사용자/관리자/대화(AI) 엔드포인트를 네임스페이스로 구분
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      # Public — no auth required
      resources :membership_plans, only: [:index]
      resources :users,            only: [:create]
      resources :sessions,         only: [:create]

      # User payment
      resources :payments, only: [:create]

      # Current user's profile / membership / 관심사
      namespace :me do
        resource :profile,    only: [:show]
        resource :membership, only: [:show]
        resource :interests,  only: [:show, :update]
      end

      # 학습(learning) 기능 — 토픽 목록
      resources :topics, only: [:index]

      # 대화(conversation) 기능 — 롤플레이 시나리오 목록
      resources :roleplay_scenarios, only: [:index]

      # Admin
      namespace :admin do
        resources :users,       only: [:index]
        resources :memberships, only: [:create, :destroy]
      end

      # AI conversation
      namespace :conversations do
        post :chat,     to: "chat#create"
        post :stt,      to: "stt#create"
        post :tts,      to: "tts#create"
        post :analysis, to: "analyses#create"
      end
    end
  end

  get "up" => "rails/health#show", as: :rails_health_check
end
