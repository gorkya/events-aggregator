from fastapi import FastAPI

from src.api.health import router as health_router

app = FastAPI(title="Events Aggregator")
app.include_router(health_router, prefix="/api")
