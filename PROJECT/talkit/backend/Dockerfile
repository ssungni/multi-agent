FROM ruby:3.3.0-slim

WORKDIR /app

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
      build-essential libpq-dev libyaml-dev curl git && \
    rm -rf /var/lib/apt/lists/*

# 컨테이너 재빌드 시에도 gem이 named volume(backend_bundle)에 유지되도록 경로 고정
ENV BUNDLE_PATH=/usr/local/bundle

COPY Gemfile Gemfile.lock ./
RUN bundle install

COPY . .

RUN chmod +x bin/rails bin/setup bin/docker-entrypoint

EXPOSE 3000

ENTRYPOINT ["bin/docker-entrypoint"]
CMD ["./bin/rails", "server", "-b", "0.0.0.0"]
