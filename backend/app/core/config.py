from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    serp_api_key: str
    groq_api_key: str
    database_url: str
    faiss_index_path: str = "./data/faiss.index"
    faiss_metadata_path: str = "./data/faiss_meta.json"
    skip_bootstrap: bool = False  # skip scrape+RAG on startup (e.g. PythonAnywhere)
    disable_scheduler: bool = False  # use cron instead of APScheduler (e.g. PythonAnywhere)

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_postgres_scheme(cls, v: str) -> str:
        """Render/Neon use postgres:// or postgresql://; we need postgresql+asyncpg://
        asyncpg does NOT accept sslmode - we strip it and use connect_args in session."""
        if not v:
            return v
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[11:]
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = "postgresql+asyncpg://" + v[13:]
        # Remove sslmode entirely - asyncpg rejects it; we use connect_args for SSL
        from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
        parsed = urlparse(v)
        if parsed.query:
            params = parse_qs(parsed.query, keep_blank_values=True)
            params.pop("sslmode", None)
            new_query = urlencode(params, doseq=True)
            parsed = parsed._replace(query=new_query)
        v = urlunparse(parsed)
        return v
    scrape_interval_hours: int = 12
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
