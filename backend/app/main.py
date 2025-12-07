"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.routes import market, portfolio, analysis, backtest, config

# Initialize FastAPI app
app = FastAPI(
    title="AI Multi-Agent Crypto Trading Simulator",
    description="A simulated crypto trading system powered by multiple LLM agents",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    # Only create tables if not in test environment
    if settings.environment != "test":
        Base.metadata.create_all(bind=engine)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Multi-Agent Crypto Trading Simulator API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "environment": settings.environment,
        "trading_mode": settings.trading_mode,
        "rule_strategy": settings.rule_strategy if settings.trading_mode == "rule" else None
    }


# Include API routers
app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(config.router)
app.include_router(analysis.router)
app.include_router(backtest.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
