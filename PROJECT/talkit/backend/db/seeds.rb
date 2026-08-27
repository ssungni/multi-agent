# 멤버십 플랜, 학습 토픽, 롤플레이 시나리오 초기 데이터를 채우는 시드 스크립트
puts "Seeding membership plans..."

MembershipPlan.find_or_create_by!(name: "Basic") do |p|
  p.feature_learning     = true
  p.feature_conversation = false
  p.feature_analysis     = false
  p.duration_days        = 30
  p.price_cents          = 129_000
  p.currency             = "KRW"
  p.active               = true
end

MembershipPlan.find_or_create_by!(name: "Premium") do |p|
  p.feature_learning     = true
  p.feature_conversation = true
  p.feature_analysis     = true
  p.duration_days        = 60
  p.price_cents          = 219_000
  p.currency             = "KRW"
  p.active               = true
end

puts "Seeding topics..."

# 콘텐츠 구조가 (간단한 한줄설명) → (이미지 + 2단락 영한 대역 리딩)으로 바뀌었으므로
# 깨끗하게 비우고 다시 채운다. (다른 테이블이 Topic을 참조하지 않아 안전하다.)
Topic.delete_all

[
  {
    category:  "월드컵",
    title:     "South Korea Keeps World Cup Hopes Alive",
    image_url: "/images/topics/01_wordcup.jpeg",
    position:  1,
    english_1: "South Korea earned an important victory in the World Cup group stage, keeping its hopes of reaching the next round alive. The team showed strong teamwork and determination throughout the match. Fans celebrated the result and expressed optimism about the upcoming games.",
    korean_1:  "대한민국은 월드컵 조별리그에서 중요한 승리를 거두며 다음 라운드 진출 가능성을 이어갔습니다. 선수들은 경기 내내 뛰어난 조직력과 투지를 보여주었습니다. 팬들은 이번 결과를 축하하며 앞으로의 경기에 대한 기대감을 나타냈습니다.",
    english_2: "After the match, the head coach praised the players for their discipline and focus. Several young players delivered impressive performances and attracted international attention. Analysts believe South Korea could become one of the tournament's surprise teams if the momentum continues.",
    korean_2:  "경기 후 감독은 선수들의 집중력과 경기 운영 능력을 높이 평가했습니다. 몇몇 젊은 선수들은 인상적인 활약을 펼치며 국제적인 주목을 받았습니다. 전문가들은 이러한 흐름이 이어진다면 대한민국이 이번 대회의 다크호스가 될 수 있다고 분석했습니다."
  },
  {
    category:  "기후 변화",
    title:     "Cities Introduce New Heatwave Protection Plans",
    image_url: "/images/topics/02_climate_change.jpeg",
    position:  2,
    english_1: "Several major cities have announced new measures to protect residents from increasingly severe heatwaves. Local governments are expanding cooling centers, planting more trees, and improving emergency response systems. Officials say these actions are necessary as extreme weather becomes more common.",
    korean_1:  "여러 주요 도시가 점점 심각해지는 폭염으로부터 시민을 보호하기 위한 새로운 대책을 발표했습니다. 지방정부는 무더위 쉼터를 확대하고, 나무를 더 심으며, 비상 대응 체계를 개선하고 있습니다. 관계자들은 극단적인 기후 현상이 증가함에 따라 이러한 조치가 필요하다고 설명했습니다.",
    english_2: "Climate experts welcomed the plans but emphasized that long-term solutions are also needed. They argue that reducing carbon emissions and investing in sustainable infrastructure will be essential for adapting to future climate challenges.",
    korean_2:  "기후 전문가들은 이러한 계획을 긍정적으로 평가하면서도 장기적인 해결책이 필요하다고 강조했습니다. 그들은 탄소 배출을 줄이고 지속 가능한 인프라에 투자하는 것이 미래 기후 위기에 대응하는 핵심이 될 것이라고 말했습니다."
  },
  {
    category:  "전기차",
    title:     "New Battery Technology Promises Faster Charging",
    image_url: "/images/topics/03_battery_technology.jpeg",
    position:  3,
    english_1: "A leading technology company has unveiled a new battery design that could significantly reduce charging times for electric vehicles. Engineers claim the battery can reach a high charge level within minutes while maintaining safety and durability.",
    korean_1:  "한 주요 기술 기업이 전기차 충전 시간을 크게 줄일 수 있는 새로운 배터리 기술을 공개했습니다. 개발진은 이 배터리가 안전성과 내구성을 유지하면서도 몇 분 안에 높은 충전 수준에 도달할 수 있다고 설명했습니다.",
    english_2: "Industry analysts believe the innovation could accelerate the adoption of electric vehicles worldwide. Faster charging may reduce one of the biggest concerns among consumers and make electric transportation more convenient.",
    korean_2:  "업계 분석가들은 이번 기술이 전 세계 전기차 보급을 더욱 가속화할 수 있다고 보고 있습니다. 빠른 충전은 소비자들의 가장 큰 걱정거리 중 하나를 해소하여 전기차 이용을 더욱 편리하게 만들 수 있습니다."
  },
  {
    category:  "우주 탐사",
    title:     "International Mission Discovers New Lunar Resources",
    image_url: "/images/topics/04_space.jpeg",
    position:  4,
    english_1: "Scientists working on an international lunar mission reported evidence of valuable resources beneath the Moon's surface. The findings may support future plans for long-term human exploration and scientific research on the Moon.",
    korean_1:  "국제 달 탐사 프로젝트에 참여한 과학자들은 달 표면 아래에서 중요한 자원의 흔적을 발견했다고 발표했습니다. 이번 발견은 장기적인 유인 탐사와 과학 연구 계획에 도움이 될 수 있습니다.",
    english_2: "Researchers say additional studies will be required before any large-scale use becomes possible. However, the discovery has already generated excitement among space agencies and private aerospace companies around the world.",
    korean_2:  "연구진은 실제 활용을 위해서는 추가 연구가 필요하다고 설명했습니다. 그럼에도 불구하고 이번 발견은 전 세계 우주 기관과 민간 우주 기업들 사이에서 큰 관심을 불러일으키고 있습니다."
  },
  {
    category:  "소셜미디어",
    title:     "New Features Aim to Improve Online Well-Being",
    image_url: "/images/topics/05_sns.jpeg",
    position:  5,
    english_1: "A popular social media platform has introduced new tools designed to encourage healthier online habits. Users can now monitor screen time, limit notifications, and receive reminders to take breaks from the app.",
    korean_1:  "한 인기 소셜미디어 플랫폼이 건강한 온라인 사용 습관을 장려하기 위한 새로운 기능을 도입했습니다. 사용자는 화면 사용 시간을 확인하고, 알림을 제한하며, 휴식을 권장하는 알림을 받을 수 있습니다.",
    english_2: "The company stated that digital well-being has become an important priority. Experts believe such features may help users develop a more balanced relationship with technology and social media platforms.",
    korean_2:  "해당 기업은 디지털 웰빙이 중요한 과제가 되었다고 밝혔습니다. 전문가들은 이러한 기능이 사용자들이 기술 및 소셜미디어와 보다 균형 잡힌 관계를 형성하는 데 도움이 될 수 있다고 평가했습니다."
  },
  {
    category:  "사이버보안",
    title:     "Major Company Strengthens Cyber Defenses",
    image_url: "/images/topics/06_security.jpeg",
    position:  6,
    english_1: "A global technology company recently announced a major upgrade to its cybersecurity systems. The new measures include advanced threat detection, employee training programs, and stronger authentication methods. Company leaders say the investment is necessary to protect customer information and digital assets.",
    korean_1:  "한 글로벌 기술 기업이 최근 사이버보안 시스템을 대폭 강화했다고 발표했습니다. 새로운 대책에는 고급 위협 탐지 기술, 직원 교육 프로그램, 강화된 인증 방식이 포함됩니다. 기업 경영진은 고객 정보와 디지털 자산을 보호하기 위해 이러한 투자가 필요하다고 설명했습니다.",
    english_2: "Cybersecurity experts welcomed the announcement and emphasized the importance of proactive security strategies. They noted that cyberattacks are becoming more sophisticated and that organizations must continuously adapt to emerging threats.",
    korean_2:  "사이버보안 전문가들은 이번 발표를 긍정적으로 평가하며 선제적인 보안 전략의 중요성을 강조했습니다. 그들은 사이버 공격이 점점 더 정교해지고 있기 때문에 기업들이 새로운 위협에 지속적으로 대응해야 한다고 말했습니다."
  },
  {
    category:  "원격근무",
    title:     "Remote Work Remains Popular Among Employees",
    image_url: "/images/topics/07_remote_working.jpeg",
    position:  7,
    english_1: "A recent survey found that many employees continue to prefer remote work arrangements. Participants reported greater flexibility, reduced commuting time, and improved work-life balance. Companies are now exploring hybrid models to meet employee expectations.",
    korean_1:  "최근 조사에 따르면 많은 직원들이 여전히 원격근무를 선호하는 것으로 나타났습니다. 응답자들은 더 큰 유연성, 출퇴근 시간 감소, 그리고 향상된 일과 삶의 균형을 장점으로 꼽았습니다. 기업들은 직원들의 기대를 충족하기 위해 하이브리드 근무 방식을 검토하고 있습니다.",
    english_2: "Business leaders acknowledge the benefits but also recognize challenges related to communication and collaboration. Many organizations are investing in digital tools to help teams stay connected and productive.",
    korean_2:  "기업 경영진은 원격근무의 장점을 인정하면서도 의사소통과 협업의 어려움 역시 인식하고 있습니다. 많은 기업들이 팀의 연결성과 생산성을 높이기 위해 디지털 도구에 투자하고 있습니다."
  },
  {
    category:  "디지털 교육",
    title:     "Online Learning Platforms Expand Globally",
    image_url: "/images/topics/08_digital_education.jpeg",
    position:  8,
    english_1: "Digital education platforms are reaching more students than ever before. New interactive tools, video lessons, and AI-powered feedback systems are helping learners access quality education regardless of location.",
    korean_1:  "디지털 교육 플랫폼은 그 어느 때보다 많은 학생들에게 도달하고 있습니다. 새로운 인터랙티브 도구, 영상 강의, AI 기반 피드백 시스템은 학습자들이 위치에 관계없이 양질의 교육을 받을 수 있도록 돕고 있습니다.",
    english_2: "Educators believe technology can support personalized learning experiences. However, they also stress the importance of maintaining student engagement and ensuring equal access to digital resources.",
    korean_2:  "교육자들은 기술이 개인 맞춤형 학습 경험을 지원할 수 있다고 믿고 있습니다. 그러나 학생들의 참여를 유지하고 디지털 자원에 대한 공평한 접근성을 보장하는 것도 중요하다고 강조합니다."
  },
  {
    category:  "의료 기술",
    title:     "AI Assists Doctors in Early Diagnosis",
    image_url: "/images/topics/09_medical.jpeg",
    position:  9,
    english_1: "Hospitals are increasingly using artificial intelligence to support medical diagnosis. Advanced systems can analyze large amounts of patient data and help identify potential health issues at an earlier stage.",
    korean_1:  "병원들은 의료 진단을 지원하기 위해 인공지능을 점점 더 많이 활용하고 있습니다. 첨단 시스템은 방대한 환자 데이터를 분석하여 건강 문제를 조기에 발견하는 데 도움을 줄 수 있습니다.",
    english_2: "Doctors emphasize that AI is designed to assist rather than replace healthcare professionals. By reducing administrative tasks and improving accuracy, the technology may allow medical staff to focus more on patient care.",
    korean_2:  "의사들은 AI가 의료진을 대체하는 것이 아니라 지원하기 위해 설계되었다고 강조합니다. 행정 업무를 줄이고 정확성을 높임으로써 의료진이 환자 치료에 더욱 집중할 수 있을 것으로 기대됩니다."
  },
  {
    category:  "반도체 산업",
    title:     "Demand for Advanced Chips Continues to Rise",
    image_url: "/images/topics/10_semiconductor.jpeg",
    position:  10,
    english_1: "The global semiconductor industry is experiencing strong demand as AI, cloud computing, and smart devices continue to expand. Manufacturers are investing heavily in new facilities and research projects.",
    korean_1:  "AI, 클라우드 컴퓨팅, 스마트 기기의 확산으로 글로벌 반도체 산업의 수요가 계속 증가하고 있습니다. 제조업체들은 새로운 생산 시설과 연구 프로젝트에 대규모 투자를 진행하고 있습니다.",
    english_2: "Industry experts predict that advanced chips will play a critical role in future technologies. Competition among countries and companies is expected to remain intense as demand grows.",
    korean_2:  "업계 전문가들은 첨단 반도체가 미래 기술의 핵심 역할을 할 것으로 전망합니다. 수요가 증가함에 따라 국가와 기업 간 경쟁도 계속 치열할 것으로 예상됩니다."
  },
  {
    category:  "로봇 기술",
    title:     "Service Robots Enter More Public Spaces",
    image_url: "/images/topics/11_robot.jpeg",
    position:  11,
    english_1: "Service robots are becoming a common sight in airports, hotels, and shopping centers. These machines can provide directions, deliver items, and assist customers with simple requests.",
    korean_1:  "서비스 로봇은 공항, 호텔, 쇼핑몰 등 다양한 공공장소에서 흔히 볼 수 있게 되었습니다. 이 로봇들은 길 안내를 하거나 물건을 전달하고 간단한 고객 요청을 처리할 수 있습니다.",
    english_2: "Developers are working to improve communication abilities and reliability. As technology advances, robots may take on more responsibilities while supporting human workers rather than replacing them.",
    korean_2:  "개발자들은 의사소통 능력과 신뢰성을 향상시키기 위해 노력하고 있습니다. 기술이 발전함에 따라 로봇은 인간 노동자를 대체하기보다는 지원하면서 더 많은 역할을 수행할 수 있을 것입니다."
  },
  {
    category:  "글로벌 경제",
    title:     "World Markets Watch Economic Trends Closely",
    image_url: "/images/topics/12_global_economic.jpeg",
    position:  12,
    english_1: "Investors around the world are paying close attention to economic indicators and policy decisions. Market movements have reflected concerns about inflation, growth, and international trade conditions.",
    korean_1:  "전 세계 투자자들은 경제 지표와 정책 결정에 큰 관심을 기울이고 있습니다. 시장 움직임은 물가 상승, 경제 성장, 국제 무역 환경에 대한 우려를 반영하고 있습니다.",
    english_2: "Economists believe long-term stability will depend on balanced policies and international cooperation. Businesses continue to adapt their strategies to changing market conditions.",
    korean_2:  "경제학자들은 장기적인 안정이 균형 잡힌 정책과 국제 협력에 달려 있다고 보고 있습니다. 기업들은 변화하는 시장 환경에 맞추어 전략을 조정하고 있습니다."
  },
  {
    category:  "스타트업",
    title:     "Startup Develops Innovative Learning Platform",
    image_url: "/images/topics/13_startup.jpeg",
    position:  13,
    english_1: "A fast-growing startup has launched an educational platform designed to make learning more interactive and personalized. The service combines AI technology with engaging digital content.",
    korean_1:  "빠르게 성장하는 한 스타트업이 학습을 더욱 흥미롭고 개인화하기 위한 교육 플랫폼을 출시했습니다. 이 서비스는 AI 기술과 매력적인 디지털 콘텐츠를 결합하고 있습니다.",
    english_2: "Investors have shown strong interest in the company, citing the growing demand for online education solutions. The startup plans to expand into international markets next year.",
    korean_2:  "투자자들은 온라인 교육 솔루션에 대한 수요 증가를 이유로 이 기업에 큰 관심을 보이고 있습니다. 해당 스타트업은 내년에 해외 시장으로 확장할 계획입니다."
  },
  {
    category:  "환경 보호",
    title:     "Community Project Restores Local Ecosystem",
    image_url: "/images/topics/14_environment.jpeg",
    position:  14,
    english_1: "Volunteers recently participated in a large environmental restoration project aimed at protecting local wildlife and natural habitats. Hundreds of trees were planted during the initiative.",
    korean_1:  "자원봉사자들은 지역 야생동물과 자연 서식지를 보호하기 위한 대규모 환경 복원 프로젝트에 참여했습니다. 이번 활동을 통해 수백 그루의 나무가 심어졌습니다.",
    english_2: "Environmental organizations praised the effort and encouraged similar projects in other regions. They believe community involvement plays a key role in long-term conservation success.",
    korean_2:  "환경 단체들은 이번 활동을 높이 평가하며 다른 지역에서도 유사한 프로젝트가 진행되기를 기대했습니다. 그들은 지역사회의 참여가 장기적인 환경 보전에 핵심적인 역할을 한다고 말했습니다."
  },
  {
    category:  "스마트 시티",
    title:     "City Launches Smart Transportation System",
    image_url: "/images/topics/15_smartcity.jpeg",
    position:  15,
    english_1: "A major city has introduced a smart transportation network that uses real-time data to improve traffic flow. Officials expect the system to reduce congestion and shorten travel times.",
    korean_1:  "한 대도시가 실시간 데이터를 활용해 교통 흐름을 개선하는 스마트 교통 시스템을 도입했습니다. 관계자들은 이 시스템이 교통 체증을 줄이고 이동 시간을 단축할 것으로 기대하고 있습니다.",
    english_2: "The project is part of a broader smart city strategy that includes energy management and public safety improvements. Residents have expressed interest in the potential benefits.",
    korean_2:  "이 프로젝트는 에너지 관리와 공공 안전 개선을 포함한 스마트 시티 전략의 일부입니다. 시민들은 이러한 변화가 가져올 긍정적인 효과에 기대를 보이고 있습니다."
  },
  {
    category:  "미래 직업",
    title:     "New Careers Emerge in the AI Era",
    image_url: "/images/topics/16_future_job.jpeg",
    position:  16,
    english_1: "As artificial intelligence becomes more common, new job opportunities are emerging across multiple industries. Companies are seeking professionals with skills in data analysis, AI management, and digital communication.",
    korean_1:  "인공지능이 보편화되면서 다양한 산업에서 새로운 직업 기회가 생겨나고 있습니다. 기업들은 데이터 분석, AI 관리, 디지털 커뮤니케이션 역량을 갖춘 인재를 찾고 있습니다.",
    english_2: "Career experts encourage workers to continue learning and adapting to technological change. Lifelong education is increasingly viewed as an essential part of professional development.",
    korean_2:  "진로 전문가들은 근로자들이 지속적으로 학습하고 기술 변화에 적응해야 한다고 조언합니다. 평생교육은 이제 직업 발전의 필수 요소로 여겨지고 있습니다."
  },
  {
    category:  "온라인 쇼핑 트렌드",
    title:     "Consumers Expect Faster Delivery Services",
    image_url: "/images/topics/17_online_shopping.jpeg",
    position:  17,
    english_1: "Online shoppers are increasingly expecting faster and more convenient delivery options. Retail companies are investing in logistics networks and automation to meet customer demands.",
    korean_1:  "온라인 쇼핑 이용자들은 점점 더 빠르고 편리한 배송 서비스를 기대하고 있습니다. 유통 기업들은 고객 수요를 충족하기 위해 물류망과 자동화 기술에 투자하고 있습니다.",
    english_2: "Analysts believe delivery speed has become a major factor in purchasing decisions. Businesses that provide reliable service may gain a competitive advantage in the market.",
    korean_2:  "전문가들은 배송 속도가 구매 결정의 중요한 요소가 되었다고 분석합니다. 신뢰할 수 있는 서비스를 제공하는 기업이 시장에서 경쟁 우위를 확보할 수 있을 것으로 보입니다."
  },
  {
    category:  "스트리밍 서비스",
    title:     "Streaming Platforms Invest in Original Content",
    image_url: "/images/topics/18_streaming_service.jpeg",
    position:  18,
    english_1: "Streaming companies are spending billions of dollars on original movies and television series. Exclusive content has become an important strategy for attracting and retaining subscribers.",
    korean_1:  "스트리밍 기업들은 오리지널 영화와 드라마 제작에 막대한 비용을 투자하고 있습니다. 독점 콘텐츠는 신규 가입자를 유치하고 기존 고객을 유지하기 위한 핵심 전략이 되었습니다.",
    english_2: "Industry observers note that competition among platforms continues to intensify. Viewers now have more choices than ever before, leading companies to focus on quality and innovation.",
    korean_2:  "업계 관계자들은 플랫폼 간 경쟁이 계속 치열해지고 있다고 분석합니다. 시청자들의 선택지가 늘어나면서 기업들은 콘텐츠 품질과 혁신에 더욱 집중하고 있습니다."
  },
  {
    category:  "e스포츠",
    title:     "International Esports Tournament Draws Millions",
    image_url: "/images/topics/19_e-sports.jpeg",
    position:  19,
    english_1: "A major esports tournament attracted millions of online viewers from around the world. Top teams competed for a prestigious championship title and a substantial prize pool.",
    korean_1:  "대규모 e스포츠 대회가 전 세계 수백만 명의 온라인 시청자를 끌어모았습니다. 최고의 팀들은 권위 있는 우승 타이틀과 거액의 상금을 놓고 경쟁했습니다.",
    english_2: "The event highlighted the rapid growth of competitive gaming and its influence on younger audiences. Sponsors and media companies continue to increase their involvement in the industry.",
    korean_2:  "이번 행사는 경쟁 게임 산업의 빠른 성장과 젊은 세대에 대한 영향력을 보여주었습니다. 후원사와 미디어 기업들도 e스포츠 산업에 대한 투자를 확대하고 있습니다."
  },
  {
    category:  "개인정보 보호",
    title:     "New Privacy Tools Give Users More Control",
    image_url: "/images/topics/20_digital_privacy.jpeg",
    position:  20,
    english_1: "Technology companies are introducing new privacy settings that allow users to better manage their personal information. The tools provide greater transparency regarding how data is collected and used.",
    korean_1:  "기술 기업들은 사용자가 자신의 개인정보를 더욱 효과적으로 관리할 수 있도록 새로운 개인정보 보호 기능을 도입하고 있습니다. 이러한 기능은 데이터 수집 및 활용 방식에 대한 투명성을 높여줍니다.",
    english_2: "Privacy advocates welcomed the changes but called for continued improvements. They argue that strong privacy protections are essential for maintaining trust in digital services.",
    korean_2:  "개인정보 보호 단체들은 이번 변화를 긍정적으로 평가하면서도 지속적인 개선이 필요하다고 주장했습니다. 그들은 강력한 개인정보 보호가 디지털 서비스에 대한 신뢰를 유지하는 데 필수적이라고 강조했습니다."
  }
].each do |attrs|
  Topic.create!(attrs)
end

puts "Seeding roleplay scenarios..."

# 전체 카탈로그를 새로 정의하므로, 이전 시드와 내용이 겹치는 경우(같은 series_title+title인데
# 속성이 다른 경우) find_or_create_by!가 기존 값을 그대로 두고 넘어가는 것을 방지하기 위해
# 깨끗하게 비우고 다시 채운다. (다른 테이블이 RoleplayScenario를 참조하지 않아 안전하다.)
RoleplayScenario.delete_all

[
  # ── 여행 영어 회화 ──────────────────────────────────────────────────────────
  { series_title: "여행 영어 회화", title: "미국 공항 입국심사", level: "Basic", position: 1,
    topic_id: "roleplay_us_immigration",
    description: "미국 공항에서 입국 심사를 받을 때 질문에 영어로 답하는 상황입니다." },
  { series_title: "여행 영어 회화", title: "공항에서 길찾기", level: "Basic", position: 2,
    topic_id: "roleplay_airport_directions",
    description: "공항 내부에서 게이트나 탑승구를 찾고 직원에게 질문하는 상황입니다." },
  { series_title: "여행 영어 회화", title: "호텔 체크인", level: "Basic", position: 3,
    topic_id: "roleplay_hotel_checkin",
    description: "호텔 프런트에서 예약을 확인하고 체크인하는 상황입니다." },
  { series_title: "여행 영어 회화", title: "호텔 체크아웃", level: "Intermediate", position: 4,
    topic_id: "roleplay_hotel_checkout",
    description: "호텔 체크아웃 시 요금 확인과 결제를 처리하는 상황입니다." },

  # ── 길찾기와 교통 ───────────────────────────────────────────────────────────
  { series_title: "길찾기와 교통", title: "길거리에서 길 묻기", level: "Basic", position: 1,
    topic_id: "roleplay_street_directions",
    description: "처음 보는 사람에게 목적지까지 가는 길을 영어로 묻는 상황입니다." },
  { series_title: "길찾기와 교통", title: "택시 목적지 설명하기", level: "Basic", position: 2,
    topic_id: "roleplay_taxi_destination",
    description: "택시 기사에게 목적지를 정확하게 설명하는 상황입니다." },
  { series_title: "길찾기와 교통", title: "지하철 노선 질문하기", level: "Intermediate", position: 3,
    topic_id: "roleplay_subway_directions",
    description: "지하철 노선과 환승 방법을 영어로 묻는 상황입니다." },
  { series_title: "길찾기와 교통", title: "버스 잘못 탑승", level: "Intermediate", position: 4,
    topic_id: "roleplay_wrong_bus",
    description: "잘못 탄 버스에서 내리거나 도움을 요청하는 상황입니다." },

  # ── 식당과 카페 ─────────────────────────────────────────────────────────────
  { series_title: "식당과 카페", title: "레스토랑 주문하기", level: "Basic", position: 1,
    topic_id: "roleplay_restaurant_order",
    description: "레스토랑에서 음식을 영어로 주문하는 상황입니다." },
  { series_title: "식당과 카페", title: "음식 잘못 나옴", level: "Intermediate", position: 2,
    topic_id: "roleplay_wrong_food",
    description: "주문한 음식과 다른 메뉴가 나왔을 때 교환 요청하는 상황입니다." },
  { series_title: "식당과 카페", title: "알레르기 설명하기", level: "Intermediate", position: 3,
    topic_id: "roleplay_allergy",
    description: "음식 알레르기나 식재료 제한을 설명하는 상황입니다." },
  { series_title: "식당과 카페", title: "카페 맞춤 주문", level: "Basic", position: 4,
    topic_id: "roleplay_cafe_order",
    description: "카페에서 음료를 원하는 방식으로 커스터마이징해서 주문하는 상황입니다." },

  # ── 직장인 필수영어 ─────────────────────────────────────────────────────────
  { series_title: "직장인 필수영어", title: "회사 첫 출근 자기소개", level: "Basic", position: 1,
    topic_id: "roleplay_first_day",
    description: "새 회사에서 동료들에게 자신을 영어로 소개하는 상황입니다." },
  { series_title: "직장인 필수영어", title: "회의에서 의견 말하기", level: "Advanced", position: 2,
    topic_id: "roleplay_meeting_opinion",
    description: "회의 중 자신의 의견을 영어로 표현하는 상황입니다." },
  { series_title: "직장인 필수영어", title: "업무 이메일 보고", level: "Intermediate", position: 3,
    topic_id: "roleplay_email_report",
    description: "상사에게 프로젝트 진행 상황을 영어 이메일로 보고하는 상황입니다." },
  { series_title: "직장인 필수영어", title: "마감 기한 연장 요청", level: "Intermediate", position: 4,
    topic_id: "roleplay_deadline_extension",
    description: "업무 데드라인 연장을 정중하게 요청하는 상황입니다." },

  # ── 일상 회화와 매너 ────────────────────────────────────────────────────────
  { series_title: "일상 회화와 매너", title: "친구 처음 만나기", level: "Basic", position: 1,
    topic_id: "roleplay_meeting_friend",
    description: "처음 만난 사람과 영어로 가볍게 대화를 시작하는 상황입니다." },
  { series_title: "일상 회화와 매너", title: "약속 시간 변경 요청", level: "Basic", position: 2,
    topic_id: "roleplay_reschedule",
    description: "친구와의 약속 시간을 영어로 조정하는 상황입니다." },
  { series_title: "일상 회화와 매너", title: "사과하기", level: "Intermediate", position: 3,
    topic_id: "roleplay_apology",
    description: "실수한 상황에서 상대방에게 영어로 사과하는 상황입니다." },
  { series_title: "일상 회화와 매너", title: "병원에서 증상 설명", level: "Intermediate", position: 4,
    topic_id: "roleplay_hospital_symptoms",
    description: "병원에서 자신의 증상을 영어로 설명하는 상황입니다." }
].each do |attrs|
  RoleplayScenario.create!(attrs)
end

puts "Done."
