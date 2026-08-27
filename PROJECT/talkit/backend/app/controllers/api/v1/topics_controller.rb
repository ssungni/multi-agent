module Api
  module V1
    # 학습용 주제(토픽) 목록 제공. learning 기능 권한이 있는 사용자만 조회 가능
    class TopicsController < ApplicationController
      def index
        return unless require_feature!(:learning)

        topics = Topic.ordered
        render json: { topics: topics.map { |t| serialize(t) } }
      end

      private

      def serialize(topic)
        {
          id:        topic.id,
          title:     topic.title,
          category:  topic.category,
          image_url: topic.image_url,
          english_1: topic.english_1,
          korean_1:  topic.korean_1,
          english_2: topic.english_2,
          korean_2:  topic.korean_2
        }
      end
    end
  end
end
