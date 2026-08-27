# OpenAI Chat Completions API로 AI 튜터와의 스트리밍 대화를 생성하는 서비스
module Ai
  class ChatService
    PRACTICE_MODE = "practice"
    LIVE_MODE     = "live"
    MODES         = [PRACTICE_MODE, LIVE_MODE].freeze

    TOPICS = {
      "self_introduction" => {
        title:    "자기소개하기",
        scenario: "Introducing One's Name and Role at Work",
        opening:  "Hi! I'm Alex, the new person here. It's nice to meet you! What's your name and what do you do?"
      },
      "daily_routine" => {
        title:    "일상 이야기",
        scenario: "Talking about your typical weekday",
        opening:  "Hey! I'm curious — what does a typical day look like for you?"
      },
      # 아래 20개는 RoleplayScenario 시드 데이터(db/seeds.rb)의 topic_id와 1:1로 매칭된다.
      # opening: 연습 모드용 — 캐릭터 대사가 아니라 상황 설명 + 시작 문장 힌트(전부 영어).
      #   사용자가 이 힌트를 참고해 한 마디 하면, 그 다음부터 LLM이 시나리오에 맞게 즉시 받아친다.
      # live_opening: 실전 모드용 — 힌트 없이 캐릭터가 바로 말을 거는 인캐릭터 대사.
      #   "전화 통화 느낌"을 살리기 위해 메타 설명 없이 곧바로 몰입하게 한다.
      "roleplay_us_immigration" => {
        title:        "미국 공항 입국심사",
        scenario:     "Practicing answering a U.S. immigration officer's questions upon arrival at the airport",
        opening:      "You've just arrived in the U.S. and an immigration officer is about to ask you some questions. You could start by saying \"Here's my passport.\" Ready to start?",
        live_opening: "Good morning. Passport, please. What is the purpose of your visit to the United States?"
      },
      "roleplay_airport_directions" => {
        title:        "공항에서 길찾기",
        scenario:     "Practicing asking airport staff for directions to a gate or boarding area",
        opening:      "You're at the airport and not sure how to find your gate. You could start with something like \"Excuse me, could you tell me how to get to gate 12?\" Ready to start?",
        live_opening: "Hi there, welcome to the information desk. How can I help you find your way today?"
      },
      "roleplay_hotel_checkin" => {
        title:        "호텔 체크인",
        scenario:     "Practicing checking in at a hotel front desk and confirming a reservation",
        opening:      "You've just arrived at a hotel and need to check in. You could start with something like \"Hi, I have a reservation under my name.\" Ready to start?",
        live_opening: "Good afternoon and welcome! Do you have a reservation with us today?"
      },
      "roleplay_hotel_checkout" => {
        title:        "호텔 체크아웃",
        scenario:     "Practicing checking out of a hotel, confirming charges, and paying the bill",
        opening:      "You're checking out of your hotel and need to settle the bill. You could start with something like \"Hi, I'd like to check out, please.\" Ready to start?",
        live_opening: "Good morning! Checking out today? Let me just confirm your charges before we finish up."
      },
      "roleplay_street_directions" => {
        title:        "길거리에서 길 묻기",
        scenario:     "Practicing asking a stranger on the street for directions to a destination",
        opening:      "You're lost on the street and need to ask a stranger for help. You could start with something like \"Excuse me, do you know where I am?\" Ready to start?",
        live_opening: "Hi there, you look like you might be searching for something. Were you trying to find your way somewhere?"
      },
      "roleplay_taxi_destination" => {
        title:        "택시 목적지 설명하기",
        scenario:     "Practicing explaining a destination clearly to a taxi driver",
        opening:      "You just got in a taxi and need to tell the driver where you're going. You could start with something like \"Could you take me to the airport, please?\" Ready to start?",
        live_opening: "Hop in! Where would you like to go today?"
      },
      "roleplay_subway_directions" => {
        title:        "지하철 노선 질문하기",
        scenario:     "Practicing asking about subway lines and transfers in English",
        opening:      "You're at the subway station and not sure which line to take. You could start with something like \"Excuse me, which line goes downtown?\" Ready to start?",
        live_opening: "Hi, you look like you're checking the subway map. Do you need help finding your route?"
      },
      "roleplay_wrong_bus" => {
        title:        "버스 잘못 탑승",
        scenario:     "Practicing realizing you're on the wrong bus and asking the driver or passengers for help",
        opening:      "You just realized you might be on the wrong bus. You could start with something like \"Excuse me, does this bus go to Central Station?\" Ready to start?",
        live_opening: "Tickets, please... is everything alright? You look a little confused about your stop."
      },
      "roleplay_restaurant_order" => {
        title:        "레스토랑 주문하기",
        scenario:     "Practicing ordering food at a restaurant in English",
        opening:      "You're at a restaurant and ready to order. You could start with something like \"I'd like to order the grilled salmon, please.\" Ready to start?",
        live_opening: "Welcome! Are you ready to order, or would you like a few more minutes with the menu?"
      },
      "roleplay_wrong_food" => {
        title:        "음식 잘못 나옴",
        scenario:     "Practicing politely asking for a dish to be corrected when the wrong food is served",
        opening:      "The server just brought you the wrong dish. You could start with something like \"Excuse me, I think this isn't what I ordered.\" Ready to start?",
        live_opening: "Here's your order! Is something wrong? You look a bit puzzled."
      },
      "roleplay_allergy" => {
        title:        "알레르기 설명하기",
        scenario:     "Practicing explaining food allergies or dietary restrictions to a server",
        opening:      "You need to let the server know about a food allergy before ordering. You could start with something like \"Before I order, I should mention I'm allergic to peanuts.\" Ready to start?",
        live_opening: "Before I take your order, is there anything you can't eat, or any allergies I should know about?"
      },
      "roleplay_cafe_order" => {
        title:        "카페 맞춤 주문",
        scenario:     "Practicing customizing a drink order at a cafe",
        opening:      "You're at a cafe and want to customize your drink order. You could start with something like \"Can I get a latte with oat milk, please?\" Ready to start?",
        live_opening: "Hi, what can I get started for you today? Any customizations to your drink?"
      },
      "roleplay_first_day" => {
        title:        "회사 첫 출근 자기소개",
        scenario:     "Practicing introducing yourself to new coworkers on your first day at work",
        opening:      "It's your first day at a new job and you're meeting your coworkers. You could start with something like \"Hi everyone, I'm excited to be here.\" Ready to start?",
        live_opening: "Hi! You must be the new team member — welcome! Want to tell us a bit about yourself?"
      },
      "roleplay_meeting_opinion" => {
        title:        "회의에서 의견 말하기",
        scenario:     "Practicing expressing and supporting your opinion clearly during a work meeting",
        opening:      "You're in a work meeting and want to share your opinion. You could start with something like \"I'd like to share a different perspective on this.\" Ready to start?",
        live_opening: "Okay team, before we move on — does anyone have thoughts on this approach?"
      },
      "roleplay_email_report" => {
        title:        "업무 이메일 보고",
        scenario:     "Practicing reporting project progress to a manager in a clear, professional tone",
        opening:      "Your manager is asking for an update on your project. You could start with something like \"The project is on track, and here's where we stand.\" Ready to start?",
        live_opening: "Hey, do you have an update for me on the project? How's it going so far?"
      },
      "roleplay_deadline_extension" => {
        title:        "마감 기한 연장 요청",
        scenario:     "Practicing politely requesting more time on a work deadline",
        opening:      "You need to ask your manager for more time on a deadline. You could start with something like \"Would it be possible to get a short extension?\" Ready to start?",
        live_opening: "Hi, I wanted to check in about that deadline — how's it looking on your end?"
      },
      "roleplay_meeting_friend" => {
        title:        "친구 처음 만나기",
        scenario:     "Practicing casual small talk when meeting someone new",
        opening:      "You're meeting someone new and starting a casual conversation. You could start with something like \"Hi, I don't think we've met before.\" Ready to start?",
        live_opening: "Hey, nice to meet you! I don't think we've talked before — what's your name?"
      },
      "roleplay_reschedule" => {
        title:        "약속 시간 변경 요청",
        scenario:     "Practicing politely asking a friend to change the time of a planned meetup",
        opening:      "You need to ask a friend to change the time of your plans. You could start with something like \"Hey, would it be okay if we moved our plans to later?\" Ready to start?",
        live_opening: "Hey! Are we still on for our plans later, or has something come up?"
      },
      "roleplay_apology" => {
        title:        "사과하기",
        scenario:     "Practicing sincerely apologizing for a mistake in English",
        opening:      "You need to sincerely apologize to someone for a mistake. You could start with something like \"I'm really sorry about what happened.\" Ready to start?",
        live_opening: "Hey... is everything okay? It seems like you wanted to talk to me about something."
      },
      "roleplay_hospital_symptoms" => {
        title:        "병원에서 증상 설명",
        scenario:     "Practicing describing symptoms to a doctor in English",
        opening:      "You're at the doctor's office and need to describe how you're feeling. You could start with something like \"I've had a headache for the past two days.\" Ready to start?",
        live_opening: "Hi, what brings you in today? Can you tell me what symptoms you've been having?"
      },

      # 아래는 AI 튜터(자유대화) 진입 시 사용자가 직접 고르는 13개 주제.
      # frontend/src/lib/tutorTopics.ts의 id와 1:1로 매칭된다.
      "tutor_travel" => {
        title:    "여행",
        scenario: "Casual conversation about travel experiences, dream destinations, and travel tips",
        opening:  "Hi! I'd love to talk about travel today. Have you been anywhere exciting recently, or is there a place you've always wanted to visit?"
      },
      "tutor_daily_life" => {
        title:    "일상과 취미",
        scenario: "Casual conversation about everyday routines and hobbies",
        opening:  "Hey there! Let's chat about everyday life. What does a typical day look like for you, and what do you enjoy doing in your free time?"
      },
      "tutor_food" => {
        title:    "음식과 요리",
        scenario: "Casual conversation about favorite foods, cooking, and dining experiences",
        opening:  "Hi! I'm curious about food today. What's your favorite dish to cook or eat, and why do you love it?"
      },
      "tutor_career" => {
        title:    "직장과 커리어",
        scenario: "Casual conversation about work, career goals, and professional life",
        opening:  "Hello! Let's talk about work and career. What do you do, and what's something you enjoy about your job?"
      },
      "tutor_tech" => {
        title:    "기술과 트렌드",
        scenario: "Casual conversation about technology, gadgets, and current trends",
        opening:  "Hi! Technology is changing so fast these days. What's a piece of technology or app you can't live without?"
      },
      "tutor_self_improvement" => {
        title:    "교육과 자기계발",
        scenario: "Casual conversation about learning, education, and personal growth",
        opening:  "Hello! Let's talk about learning and growth. Is there a skill you're trying to improve right now?"
      },
      "tutor_society" => {
        title:    "사회와 가치관",
        scenario: "Casual conversation about social issues and personal values",
        opening:  "Hi! I'd like to hear your thoughts on something — what's a value or belief that's really important to you?"
      },
      "tutor_sports" => {
        title:    "운동과 스포츠",
        scenario: "Casual conversation about exercise habits and favorite sports",
        opening:  "Hey! Let's talk fitness and sports. Do you play or watch any sports, or have a favorite way to stay active?"
      },
      "tutor_music" => {
        title:    "음악",
        scenario: "Casual conversation about music tastes and favorite artists",
        opening:  "Hi! Music is one of my favorite topics. What kind of music do you usually listen to?"
      },
      "tutor_reading" => {
        title:    "독서",
        scenario: "Casual conversation about books and reading habits",
        opening:  "Hello! Do you enjoy reading? Tell me about a book you've read recently or one you'd recommend."
      },
      "tutor_youtube" => {
        title:    "유튜브",
        scenario: "Casual conversation about YouTube channels and video content",
        opening:  "Hi! What kind of YouTube videos do you usually watch? Any channels you'd recommend?"
      },
      "tutor_drama_movie" => {
        title:    "드라마와 영화",
        scenario: "Casual conversation about movies, dramas, and TV shows",
        opening:  "Hey! Let's talk movies and shows. What's something you've watched recently that you really liked?"
      },
      "tutor_environment" => {
        title:    "기후, 환경, 자연",
        scenario: "Casual conversation about climate, environment, and nature",
        opening:  "Hi! I'd like to talk about nature and the environment today. Do you do anything in your daily life to be more eco-friendly?"
      }
    }.freeze

    SYSTEM_PROMPT = <<~PROMPT.freeze
      You are Alex, a friendly and encouraging English tutor from Talkit.
      Your role is to help the user practice conversational English naturally.

      ## Rules
      - Keep each response to 2-3 sentences maximum
      - Gently correct grammar errors by naturally rephrasing (e.g. "You mean you are a developer — great!")
      - Always end with a follow-up question to sustain conversation
      - Prioritize building your follow-up question on whatever the user just said;
        fall back to the Topic/Interests given below only when their reply doesn't give you much to work with
      - Respond in English only
      - Adapt vocabulary complexity to the user's apparent level
      - Do not repeat the same question twice
    PROMPT

    def initialize(messages:, topic_id: nil, interests: [], wrap_up: false, mode: PRACTICE_MODE)
      @messages  = messages
      @interests = interests.to_a
      # topic_id가 명시적으로 주어질 때만(롤플레이 시나리오 등) 단일 시나리오를 쓴다.
      # 없으면 사용자의 저장된 관심사(또는 일반 자유대화)로 폴백한다.
      @topic     = TOPICS[topic_id.to_s]
      # 세션 30분 한도에 도달했을 때, 이번 응답에서만 자연스럽게 작별 인사로 마무리하도록
      # 지시를 한 번 추가한다 (대화 중간에 끊지 않고, AI 턴에서 자연스럽게 종료).
      @wrap_up   = wrap_up
      # 실전 모드("전화 통화 느낌")는 피드백 줄이 끼어들면 몰입이 깨지므로, 롤플레이의
      # 피드백 지시는 연습 모드에서만 추가한다. 클라이언트가 보낸 값이 알려진 모드가
      # 아니면(오타 등) 조용히 연습 모드로 폴백한다.
      @mode      = MODES.include?(mode) ? mode : PRACTICE_MODE
      @client    = OpenAI::Client.new(access_token: ENV.fetch("OPENAI_API_KEY"))
    end

    # OpenAI 응답을 스트리밍으로 받아 delta 텍스트가 생길 때마다 block을 호출
    # ruby-openai 7.x부터는 stream:에 do...end 블록이 아니라 parameters 안에
    # Proc을 직접 넘겨야 한다 ("stream parameter must be a Proc" 에러 방지).
    def stream(&block)
      streaming_proc = proc do |chunk, _bytesize|
        delta = chunk.dig("choices", 0, "delta", "content")
        block.call(delta) if delta
      end

      @client.chat(
        parameters: {
          model:      "gpt-4o",
          messages:   build_messages,
          stream:     streaming_proc,
          max_tokens: 256
        }
      )
    end

    private

    # OpenAI에 전달할 messages 배열을 생성
    def build_messages
      # 시스템 프롬프트와 주제/관심사 정보, (필요 시) 마무리 지시를 하나의 문자열로 합침
      sections = [SYSTEM_PROMPT, topic_or_interests_section]
      sections << wrap_up_section if @wrap_up
      system_content = sections.join("\n")

      # system 메시지를 맨 앞에 추가하고,
      # 기존 대화 메시지(@messages)를 뒤에 이어서 반환
      [{ role: "system", content: system_content }, *@messages]
    end

    # 세션 시간 한도(30분)에 도달했을 때만 추가되는 일회성 지시 — 이 응답에서
    # 자연스럽게 작별 인사를 하고 대화를 마무리하도록 한다.
    def wrap_up_section
      [
        "## Wrap up",
        "This conversation has reached its time limit for this session.",
        "In this response, naturally wrap up the conversation — say a warm goodbye and suggest continuing again tomorrow.",
        "Do not ask a follow-up question. Keep it brief and natural."
      ].join("\n")
    end

    # 현재 대화에 사용할 Topic 또는 사용자 관심사 정보를 생성
    def topic_or_interests_section
      if @topic
        # AI 롤플레이 — 자유대화(AI 튜터)와 달리 주어진 상황에 집중해야 하므로,
        # 사용자가 주제에서 벗어나면 캐릭터를 유지한 채 자연스럽게 시나리오로 되돌아오게 한다.
        lines = [
          "## Topic",
          "Title: #{@topic[:title]}",
          "Scenario: #{@topic[:scenario]}",
          "Stay focused on this scenario and stay in character. If the user goes off-topic, " \
          "gently steer the conversation back to the scenario in character, without breaking immersion."
        ]
        # 실전 모드는 "전화 통화 느낌"이 핵심이라 피드백 줄이 끼어들면 몰입이 깨진다 —
        # 연습 모드에서만 피드백 지시를 추가하고, 실전 모드는 SYSTEM_PROMPT의 일반 교정
        # 규칙("Gently correct grammar errors...")까지 명시적으로 덮어써서 피드백을 끈다.
        if @mode == PRACTICE_MODE
          lines << (
            "If there's a grammar or phrasing correction worth making, put it on its own line first " \
            "(one short sentence), then a line break, then your in-character reply on the next line " \
            "(one sentence). If there's nothing to correct, skip the feedback line and just reply in character."
          )
        else
          lines << (
            "This is the live mode — treat it like a real phone call. Do not give any language " \
            "feedback or break character to comment on the user's English. Respond only as the " \
            "character in this scenario."
          )
        end
        lines.join("\n")
      else
        # AI 튜터 (관심사 선택) — 저장된 interest id가 더 이상 TOPICS에 없는 키라면
        # (토픽 제거 등) titles가 비어버릴 수 있으므로, 그 경우에도 일반 대화로 폴백한다.
        titles = @interests.filter_map { |id| TOPICS.dig(id, :title) }
        if titles.any?
          [
            "## User's interests",
            "The user has shown interest in: #{titles.join(', ')}.",
            "Use these as inspiration for follow-up questions when needed, without forcing an abrupt topic switch."
          ].join("\n")
        else
          # AI 튜터 (관심사 선택하지 X, 또는 선택한 관심사를 모두 찾지 못함)
          ["## Topic", "Title: General conversation", "Scenario: Free-flowing casual conversation — get to know the user"].join("\n")
        end
      end
    end
  end
end
