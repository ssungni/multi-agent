# 모든 모델이 상속하는 추상 베이스 클래스
class ApplicationRecord < ActiveRecord::Base
  primary_abstract_class
end
