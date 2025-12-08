"""
Configuration management for the trading simulator.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str
    
    # LLM Configuration (Optional - if not provided, only rule-based mode available)
    llm_api_key: Optional[str] = None
    llm_provider: str = "openrouter"  # "openai" or "openrouter"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    daily_token_budget: int = 100000
    cheap_model: str = "deepseek/deepseek-chat"  # For analysts
    strong_model: str = "deepseek/deepseek-chat"  # For researcher, trader, risk manager
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    
    # Binance API (Production - for market data only)
    binance_base_url: str = "https://api.binance.com"
    
    # Binance Testnet API (Paper Trading)
    # Get your testnet API keys from: https://testnet.binance.vision/
    binance_testnet_enabled: bool = False  # Set to True to use testnet
    binance_testnet_base_url: str = "https://testnet.binance.vision"
    binance_testnet_api_key: Optional[str] = None
    binance_testnet_api_secret: Optional[str] = None
    
    # Trading Simulation (for local simulation when testnet disabled)
    initial_cash: float = 10000.0
    max_position_size_pct: float = 0.10
    max_total_exposure_pct: float = 0.80
    
    # Paper Trading Configuration
    paper_trading_enabled: bool = True
    paper_trading_mode: str = "testnet"  # Options: "testnet" (real Binance API) or "simulation" (local)
    
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
    
    @property
    def llm_enabled(self) -> bool:
        """Check if LLM mode is available based on API key presence."""
        return bool(self.llm_api_key and self.llm_api_key.strip())
    
    @property
    def default_engine_mode(self) -> str:
        """Return default engine mode: 'llm' if available, otherwise 'rule'."""
        return "llm" if self.llm_enabled else "rule"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
