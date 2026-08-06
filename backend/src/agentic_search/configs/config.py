from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    从 .env 文件中读取配置
    """

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra = "ignore",
    )

    llm_model: str = "mimo-v2.5"
    llm_model_provider: str = "openai"
    llm_base_url: str = "https://token-plan-cn.xiaomimimo.com/v1"
    llm_api_key: str = ""
    llm_timeout: int = 60


    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "agentic_search"

settings = Settings()
# 基类