from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    serp_api_key: str
    groq_api_key: str
    database_url: str
    faiss_index_path: str

    faiss_metadata_path: str

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_postgres_scheme(cls, v: str) -> str:
        """Render/Heroku use postgres://; SQLAlchemy asyncpg needs postgresql+asyncpg://"""
        if v and v.startswith("postgres://"):
            return "postgresql+asyncpg://" + v[11:]
        return v
    scrape_interval_hours: int = 12
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
