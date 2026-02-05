from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    cerebras_api_key: str
    cerebras_model: str = "glm-4.7"
    rate_limit_requests: int = 2
    rate_limit_concurrent: int = 2
    api_timeout: int = 30
    filter_budget_min: int = 500
    checkpoint_interval: int = 10
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()