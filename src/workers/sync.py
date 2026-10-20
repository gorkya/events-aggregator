import asyncio
import logging

from src.clients.events_provider import EventsProviderClient
from src.clients.paginator import EventsPaginator
from src.core.db import session_factory
from src.repositories.events import EventRepository
from src.repositories.sync_state import SyncStateRepository
from src.usecases.sync_events import SyncEventsUsecase

logger = logging.getLogger(__name__)

SYNC_INTERVAL_SECONDS = 24 * 60 * 60


class SyncRunner:
    def __init__(self, client: EventsProviderClient) -> None:
        self._client = client
        self._lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        return self._lock.locked()

    def _events_source(self, changed_at: str) -> EventsPaginator:
        return EventsPaginator(self._client, changed_at)

    async def run(self) -> bool:
        """Запускает синхронизацию. False, если другая уже идёт."""
        if self._lock.locked():
            return False
        async with self._lock:
            async with (
                session_factory() as events_session,
                session_factory() as state_session,
            ):
                usecase = SyncEventsUsecase(
                    events_source=self._events_source,
                    events=EventRepository(events_session),
                    state=SyncStateRepository(state_session),
                )
                try:
                    await usecase.do()
                except Exception as ex:
                    logger.exception(f"Sync run failed with exception: {ex}")
        return True


async def run_periodically(runner: SyncRunner) -> None:
    while True:
        await runner.run()
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)
