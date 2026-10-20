import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from sqlalchemy import text

from src.api.health import router as health_router
from src.api.sync import router as sync_router
from src.clients.events_provider import EventsProviderClient
from src.core.config import settings
from src.core.db import engine
from src.workers.sync import SyncRunner, run_periodically

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    client = EventsProviderClient(
        base_url=settings.events_provider_url,
        api_key=settings.events_provider_api_key,
    )
    runner = SyncRunner(client)
    app.state.sync_runner = runner
    sync_task = asyncio.create_task(run_periodically(runner))

    yield

    sync_task.cancel()
    with suppress(asyncio.CancelledError):
        await sync_task
    await client.aclose()
    await engine.dispose()


app = FastAPI(title="Events Aggregator", lifespan=lifespan)
app.include_router(health_router, prefix="/api")
app.include_router(sync_router, prefix="/api")
