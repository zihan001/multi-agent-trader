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
    
    # Trading Mode Configuration (Phase 6)
    trading_mode: str = "llm"  # Options: "llm" or "rule"
    
    # Rule-Based Strategy Configuration (for trading_mode="rule")
    rule_strategy: str = "rsi_macd"  # Options: "rsi_macd", "ema_crossover", "bb_volume"
    
    # RSI Strategy Parameters
    rsi_period: int = 14
    rsi_oversold: int = 30
    rsi_overbought: int = 70
    
    # MACD Strategy Parameters
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    
    # EMA Strategy Parameters
    ema_fast: int = 9
    ema_slow: int = 21
    ema_trend: int = 50
    
    # Bollinger Bands Strategy Parameters
    bb_period: int = 20
    bb_std: float = 2.0
    
    # Volume Analysis Parameters
    volume_ma_period: int = 20
    volume_surge_threshold: float = 1.5  # 1.5x average volume
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
