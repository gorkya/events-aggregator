from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from src.api.health import router as health_router
from src.core.db import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    await engine.dispose()


app = FastAPI(title="Events Aggregator", lifespan=lifespan)
app.include_router(health_router, prefix="/api")
