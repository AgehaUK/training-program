from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/failure_analysis"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    secret_key: str = "changeme-secret-key"

    class Config:
        env_file = ".env"


settings = Settings()
