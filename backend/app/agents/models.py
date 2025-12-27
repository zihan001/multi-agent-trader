"""
Pydantic models for structured agent outputs.

These models ensure type-safe, validated responses from LLM agents.
"""
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class KeyLevels(BaseModel):
    """Support and resistance price levels."""
    support: List[float] = Field(description="Support price levels")
    resistance: List[float] = Field(description="Resistance price levels")


class IndicatorsSummary(BaseModel):
    """Summary of technical indicators."""
    rsi: str = Field(description="RSI interpretation")
    macd: str = Field(description="MACD interpretation")
    emas: str = Field(description="EMA alignment interpretation")


class TechnicalAnalysis(BaseModel):
    """Structured output for Technical Analyst."""
    thought_process: Any = Field(description="Step-by-step reasoning process (can be string or structured object)")
    trend: Literal["bullish", "bearish", "sideways", "uncertain"] = Field(
        description="Overall market trend direction"
    )
    strength: Literal["strong", "moderate", "weak"] = Field(
        description="Strength of the identified trend"
    )
    key_levels: Optional[KeyLevels] = Field(default=None, description="Support and resistance levels")
    indicators_summary: Optional[IndicatorsSummary] = Field(default=None, 
        description="Summary of technical indicators"
    )
    momentum: str = Field(description="Momentum assessment")
    volume_analysis: str = Field(description="Volume pattern analysis")
    key_observations: List[str] = Field(
        description="Key technical observations",
        default_factory=list
    )
    recommendation: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"] = Field(
        description="Trading recommendation"
    )
    confidence: int = Field(
        description="Confidence level in the analysis",
        ge=0,
        le=100
    )
    reasoning: str = Field(description="Concise reasoning for recommendation")
    risk_factors: List[str] = Field(
        description="Identified risk factors",
        default_factory=list
    )


class KeyFactors(BaseModel):
    """Sentiment key factors."""
    social_media: str = Field(description="Social media sentiment")
    news_coverage: str = Field(description="News coverage sentiment")
    fear_greed: str = Field(description="Fear & Greed index interpretation")
    volume_interest: str = Field(description="Volume and interest level")


class SentimentAnalysis(BaseModel):
    """Structured output for Sentiment Analyst."""
    thought_process: str = Field(description="Step-by-step reasoning process")
    overall_sentiment: Literal["bullish", "bearish", "neutral"] = Field(
        description="Overall market sentiment"
    )
    sentiment_score: int = Field(
        description="Sentiment score from -100 (very bearish) to 100 (very bullish)",
        ge=-100,
        le=100
    )
    sentiment_strength: Literal["extreme", "strong", "moderate", "weak"] = Field(
        description="Strength of sentiment"
    )
    key_factors: KeyFactors = Field(description="Breakdown of sentiment factors")
    contrarian_signals: List[str] = Field(
        description="Contrarian signals indicating potential reversals",
        max_items=5
    )
    crowd_psychology: str = Field(description="Crowd psychology assessment")
    sentiment_trend: Literal["improving", "deteriorating", "stable"] = Field(
        description="Sentiment trend direction"
    )
    key_observations: List[str] = Field(
        description="Key sentiment observations",
        min_items=1,
        max_items=5
    )
    trading_implication: str = Field(description="Trading implications of sentiment")
    confidence: int = Field(
        description="Confidence level in the analysis",
        ge=0,
        le=100
    )
    reasoning: str = Field(description="Reasoning for assessment")
    risk_factors: List[str] = Field(
        description="Sentiment-related risks",
        max_items=5
    )


class SupplyAnalysis(BaseModel):
    """Token supply analysis."""
    inflation_rate: str = Field(description="Token inflation rate")
    supply_distribution: str = Field(description="Token distribution analysis")
    unlock_schedule: str = Field(description="Token unlock schedule")


class LiquidityAnalysis(BaseModel):
    """Liquidity analysis."""
    market_cap_size: str = Field(description="Market cap classification")
    trading_liquidity: str = Field(description="Trading liquidity assessment")
    volume_quality: str = Field(description="Volume quality analysis")


class UtilityAssessment(BaseModel):
    """Token utility assessment."""
    use_cases: str = Field(description="Token use cases")
    network_activity: str = Field(description="Network activity level")
    real_world_adoption: str = Field(description="Real-world adoption status")


class TokenomicsAnalysis(BaseModel):
    """Structured output for Tokenomics Analyst."""
    thought_process: str = Field(description="Step-by-step reasoning process")
    fundamental_rating: Literal["strong", "moderate", "weak", "poor"] = Field(
        description="Overall fundamental rating"
    )
    value_assessment: Literal["undervalued", "fairly_valued", "overvalued"] = Field(
        description="Valuation assessment"
    )
    supply_analysis: SupplyAnalysis = Field(description="Supply dynamics analysis")
    liquidity_analysis: LiquidityAnalysis = Field(description="Liquidity analysis")
    utility_assessment: UtilityAssessment = Field(description="Utility assessment")
    competitive_position: str = Field(description="Competitive positioning")
    strengths: List[str] = Field(
        description="Fundamental strengths",
        max_items=5
    )
    weaknesses: List[str] = Field(
        description="Fundamental weaknesses",
        max_items=5
    )
    key_risks: List[str] = Field(
        description="Key risk factors",
        max_items=5
    )
    key_observations: List[str] = Field(
        description="Key tokenomics observations",
        min_items=1,
        max_items=5
    )
    long_term_outlook: Literal["bullish", "neutral", "bearish"] = Field(
        description="Long-term fundamental outlook"
    )
    trading_implication: str = Field(description="Trading implications")
    confidence: int = Field(
        description="Confidence level in the analysis",
        ge=0,
        le=100
    )
    reasoning: str = Field(description="Reasoning for assessment")


class AnalystSummary(BaseModel):
    """Summary of analyst confidence levels."""
    technical_confidence: int = Field(ge=0, le=100)
    sentiment_confidence: int = Field(ge=0, le=100)
    tokenomics_confidence: int = Field(ge=0, le=100)
    agreement_level: str = Field(description="Level of agreement between analysts")


class AnalysisSynthesis(BaseModel):
    """Synthesis of different analyses."""
    technical_weight: float = Field(ge=0, le=1, description="Weight given to technical")
    sentiment_weight: float = Field(ge=0, le=1, description="Weight given to sentiment")
    fundamental_weight: float = Field(ge=0, le=1, description="Weight given to fundamentals")
    primary_driver: str = Field(description="Primary decision driver")
    conflict_resolution: str = Field(description="How conflicts were resolved")


class OpportunityAssessment(BaseModel):
    """Assessment of trading opportunity quality."""
    setup_quality: str = Field(description="Quality of the trading setup")
    risk_reward: str = Field(description="Risk-reward assessment")
    timing: str = Field(description="Timing assessment")


class ResearchSynthesis(BaseModel):
    """Structured output for Researcher."""
    thought_process: str = Field(description="Step-by-step synthesis reasoning")
    analyst_summary: AnalystSummary = Field(description="Summary of analyst inputs")
    thesis_summary: str = Field(description="Unified investment thesis")
    market_view: Literal[
        "strongly_bullish", "bullish", "neutral", "bearish", "strongly_bearish"
    ] = Field(description="Overall market view")
    conviction_level: Literal["high", "medium", "low"] = Field(
        description="Conviction level in the thesis"
    )
    time_horizon: Literal["short_term", "medium_term", "long_term", "mixed"] = Field(
        description="Appropriate time horizon"
    )
    analysis_synthesis: AnalysisSynthesis = Field(
        description="How different analyses were synthesized"
    )
    key_bull_cases: List[str] = Field(
        description="Key bullish arguments",
        min_items=1,
        max_items=5
    )
    key_bear_cases: List[str] = Field(
        description="Key bearish arguments",
        min_items=1,
        max_items=5
    )
    signal_conflicts: str = Field(description="Description of conflicting signals")
    catalyst_watch: List[str] = Field(
        description="Catalysts to watch",
        max_items=5
    )
    risk_factors: List[str] = Field(
        description="Key risk factors",
        max_items=5
    )
    opportunity_assessment: OpportunityAssessment = Field(
        description="Quality of the opportunity"
    )
    recommended_action: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"] = Field(
        description="Recommended action"
    )
    confidence: int = Field(
        description="Overall confidence level",
        ge=0,
        le=100
    )
    reasoning: str = Field(description="Final reasoning")


class ConvictionCheck(BaseModel):
    """Conviction threshold check."""
    research_confidence: int = Field(ge=0, le=100)
    passes_threshold: bool = Field(description="Whether conviction passes minimum threshold")
    size_justification: str = Field(description="Justification for position size")


class EntryStrategy(BaseModel):
    """Entry strategy details."""
    recommended_price: float = Field(description="Recommended entry price")
    price_range: Dict[str, float] = Field(description="Price range for entry")
    order_type: str = Field(description="Recommended order type")
    timing: str = Field(description="Execution timing recommendation")


class PositionSizing(BaseModel):
    """Position sizing details."""
    recommended_size_usd: float = Field(description="Recommended size in USD", ge=0)
    recommended_size_pct: float = Field(description="Recommended size as % of portfolio", ge=0, le=100)
    rationale: str = Field(description="Rationale for position size")


class ExitStrategy(BaseModel):
    """Exit strategy details."""
    take_profit_levels: List[float] = Field(description="Take profit price levels", min_items=1)
    stop_loss: float = Field(description="Stop loss price")
    trailing_stop: Optional[float] = Field(description="Trailing stop percentage", default=None)


class RiskAssessment(BaseModel):
    """Risk assessment details."""
    max_loss_usd: float = Field(description="Maximum loss in USD")
    max_loss_pct: float = Field(description="Maximum loss as % of entry")
    reward_risk_ratio: float = Field(description="Reward to risk ratio", ge=0)
    key_risks: List[str] = Field(description="Key risks for this trade", max_items=5)


class TradeProposal(BaseModel):
    """Structured output for Trader."""
    thought_process: str = Field(description="Step-by-step trade planning reasoning")
    action: Literal["buy", "sell", "hold", "close"] = Field(
        description="Proposed action"
    )
    urgency: Literal["immediate", "soon", "no_rush", "hold"] = Field(
        description="Execution urgency"
    )
    trade_rationale: str = Field(description="Rationale for the trade")
    conviction_check: ConvictionCheck = Field(description="Conviction threshold validation")
    entry_strategy: EntryStrategy = Field(description="Entry strategy details")
    position_sizing: PositionSizing = Field(description="Position sizing details")
    exit_strategy: ExitStrategy = Field(description="Exit strategy details")
    risk_assessment: RiskAssessment = Field(description="Risk assessment")
    execution_notes: str = Field(description="Execution notes and considerations")
    time_horizon: Literal["scalp", "day_trade", "swing", "position"] = Field(
        description="Trade time horizon"
    )
    confidence: int = Field(
        description="Confidence in the trade proposal",
        ge=0,
        le=100
    )
    reasoning: str = Field(description="Final reasoning")


class RiskCheck(BaseModel):
    """Individual risk rule check result."""
    passes: bool = Field(description="Whether the check passed")
    value: float = Field(description="Actual value")
    limit: float = Field(description="Limit/threshold")
    details: str = Field(description="Details about the check")


class RiskAssessmentChecks(BaseModel):
    """Complete risk assessment checks."""
    position_size_check: RiskCheck
    exposure_check: RiskCheck
    stop_loss_check: RiskCheck
    risk_reward_check: RiskCheck
    concentration_check: RiskCheck
    conviction_check: RiskCheck


class Modifications(BaseModel):
    """Proposed modifications to trade."""
    position_size_usd: Optional[float] = Field(default=None)
    stop_loss: Optional[float] = Field(default=None)
    take_profit: Optional[float] = Field(default=None)
    reasoning: str = Field(description="Reasoning for modifications")


class FinalTrade(BaseModel):
    """Final validated trade parameters."""
    action: Literal["buy", "sell", "hold", "close"]
    size_usd: float = Field(ge=0)
    entry_price: Optional[float] = Field(default=None)
    stop_loss: Optional[float] = Field(default=None)
    take_profit: Optional[float] = Field(default=None)
    max_loss_pct: float = Field(description="Maximum loss percentage")


class RiskMetrics(BaseModel):
    """Calculated risk metrics."""
    position_size_pct: float = Field(description="Position size as % of portfolio")
    new_total_exposure_pct: float = Field(description="New total exposure %")
    max_loss_usd: float = Field(description="Maximum loss in USD")
    max_loss_pct_portfolio: float = Field(description="Max loss as % of portfolio")
    risk_reward_ratio: float = Field(description="Risk-reward ratio")
    passes_all_checks: bool = Field(description="Whether all checks passed")


class RiskValidation(BaseModel):
    """Structured output for Risk Manager."""
    thought_process: str = Field(description="Step-by-step validation reasoning")
    decision: Literal["approved", "rejected", "modified"] = Field(
        description="Risk management decision"
    )
    risk_assessment: RiskAssessmentChecks = Field(
        description="Detailed risk assessment checks"
    )
    modifications: Modifications = Field(description="Proposed modifications")
    final_trade: Optional[FinalTrade] = Field(
        description="Final trade parameters (null if rejected)",
        default=None
    )
    risk_metrics: RiskMetrics = Field(description="Calculated risk metrics")
    concerns: List[str] = Field(
        description="Risk concerns identified",
        max_items=5
    )
    recommendations: List[str] = Field(
        description="Risk management recommendations",
        max_items=5
    )
    rejection_reason: Optional[str] = Field(
        description="Reason for rejection if applicable",
        default=None
    )
    confidence: int = Field(
        description="Confidence in risk assessment",
        ge=0,
        le=100
    )
    reasoning: str = Field(description="Final risk reasoning")
