from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    supabase_url: str = "http://127.0.0.1:54321"
    supabase_service_key: str = ""

    ollama_host: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_chat_model: str = "llama3.1"

    # Comma-separated list, e.g. "brave,reddit"
    search_providers: str = "brave"
    brave_api_key: str = ""

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "research-orchestrator/0.1"

    sec_user_agent: str = "research-orchestrator ujculbe@gmail.com"


settings = Settings()
