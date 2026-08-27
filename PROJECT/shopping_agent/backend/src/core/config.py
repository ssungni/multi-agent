from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    REDIS_URL: str = "redis://localhost:6379/0"
    ANTHROPIC_API_KEY: str = ""
    # 로컬 개발은 http라 Secure 쿠키가 전송되지 않음 — 배포 시 HTTPS 뒤에서 반드시 true로 설정
    COOKIE_SECURE: bool = False


settings = Settings()
