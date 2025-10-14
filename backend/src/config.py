"""Application configuration."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Reddit API
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str = "SentimentAgent/1.0"
    
    # Azure CosmosDB
    cosmos_endpoint: str
    cosmos_key: str
    cosmos_database: str = "sentiment_analysis"
    cosmos_container_posts: str = "reddit_posts"
    cosmos_container_comments: str = "reddit_comments"
    cosmos_container_sentiment: str = "sentiment_scores"
    cosmos_container_trending: str = "trending_topics"
    
    # Azure OpenAI (Optional)
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str = "gpt-4"
    azure_openai_api_version: str = "2024-02-01"
    
    # Sentiment Analysis
    sentiment_method: str = "VADER"  # VADER or LLM
    use_llm_for_ambiguous: bool = False
    
    # Data Collection
    collection_interval_minutes: int = 30
    subreddits: str = "Cursor,Bard,GithubCopilot,claude,windsurf,ChatGPTCoding,vibecoding,aws,programming,MachineLearning,artificial,OpenAI,kiroIDE,JulesAgent"
    
    # Data Retention
    data_retention_days: int = 90
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # Logging
    log_level: str = "INFO"
    
    @property
    def subreddit_list(self) -> List[str]:
        """Get list of subreddits to monitor."""
        return [s.strip() for s in self.subreddits.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get list of allowed CORS origins."""
        return [o.strip() for o in self.api_cors_origins.split(",")]


settings = Settings()
