"""
Ultra-simplified eBay Manager FastAPI Application - YAGNI compliant
90% complexity reduction: 271 → 30 lines
Following successful Phases 2-4 pattern
"""

from fastapi import FastAPI
from app.core.config import settings
from app.api.auth import router as auth_router

# Simple FastAPI app
app = FastAPI(
    title="eBay Manager API",
    description="Ultra-simplified eBay management system",
    version="1.0.0"
)

# Include essential routers only
app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
def root():
    """Simple root endpoint"""
    return {"message": "eBay Manager API", "version": "1.0.0"}

@app.get("/ping")
def ping():
    """Simple ping endpoint"""
    return "pong"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)