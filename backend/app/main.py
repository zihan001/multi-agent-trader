"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.routes import market, portfolio

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="AI Multi-Agent Crypto Trading Simulator",
    description="A simulated crypto trading system powered by multiple LLM agents",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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
        "environment": settings.environment
    }


# Include API routers
app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])


# TODO: Import and include remaining routers when they are created
# from app.routes import analysis, backtest
# app.include_router(analysis.router, prefix="/analyze", tags=["analysis"])
# app.include_router(backtest.router, prefix="/backtest", tags=["backtest"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
