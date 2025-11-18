"""
Configuration management for the trading simulator.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str
    
    # LLM Configuration
    llm_api_key: str
    llm_provider: str = "openrouter"  # "openai" or "openrouter"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    daily_token_budget: int = 100000
    cheap_model: str = "deepseek/deepseek-chat"  # For analysts
    strong_model: str = "deepseek/deepseek-chat"  # For researcher, trader, risk manager
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    
    # Binance API
    binance_base_url: str = "https://api.binance.com"
    
    # Trading Simulation
    initial_cash: float = 10000.0
    max_position_size_pct: float = 0.10
    max_total_exposure_pct: float = 0.80
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
