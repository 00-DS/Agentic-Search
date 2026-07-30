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
    llm_timeout: int = 30

    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "agentic_search"

settings = Settings()