import asyncio
import logging
from contextlib import asynccontextmanager, suppress

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.api.events import router as events_router
from src.api.health import router as health_router
from src.api.sync import router as sync_router
from src.api.tickets import router as tickets_router
from src.clients.events_provider import EventsProviderClient
from src.core.cache import TTLCache
from src.core.config import settings
from src.core.db import engine
from src.workers.sync import SyncRunner, run_periodically

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

SEATS_CACHE_TTL_SECONDS = 30


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    client = EventsProviderClient(
        base_url=settings.events_provider_url,
        api_key=settings.events_provider_api_key,
    )
    runner = SyncRunner(client)
    app.state.events_client = client
    app.state.seats_cache = TTLCache[list[str]](SEATS_CACHE_TTL_SECONDS)
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
app.include_router(events_router, prefix="/api")
app.include_router(tickets_router, prefix="/api")


@app.exception_handler(httpx.HTTPError)
async def provider_error_handler(
    request: Request, exc: httpx.HTTPError
) -> JSONResponse:
    logger.error("Events provider error: %r", exc)
    return JSONResponse(
        status_code=502, content={"detail": "Events provider unavailable"}
    )
