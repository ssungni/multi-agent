module Api
  module V1
    # 롤플레잉 시나리오 목록 제공. conversation 기능 권한이 있는 사용자만 조회 가능
    class RoleplayScenariosController < ApplicationController
      def index
        return unless require_feature!(:conversation)

        scenarios = RoleplayScenario.ordered
        render json: { roleplay_scenarios: scenarios.map { |s| serialize(s) } }
      end

      private

      # 시나리오에 연결된 주제의 오프닝 대사(opening/live_opening)를 함께 내려줌
      def serialize(scenario)
        topic = Ai::ChatService::TOPICS[scenario.topic_id]
        {
          id:           scenario.id,
          series_title: scenario.series_title,
          title:        scenario.title,
          level:        scenario.level,
          description:  scenario.description,
          position:     scenario.position,
          topic_id:     scenario.topic_id,
          opening:      topic&.fetch(:opening, nil),
          live_opening: topic&.fetch(:live_opening, nil)
        }
      end
    end
  end
end
