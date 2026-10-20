import logging
import typing
from collections.abc import AsyncIterable, Callable
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from src.domain import EventData, PlaceData, SyncState

logger = logging.getLogger(__name__)

FIRST_SYNC_DATE = "2000-01-01"
BATCH_SIZE = 100


class EventRepository(typing.Protocol):
    async def upsert_many(self, events: list[EventData]) -> None: ...


class SyncStateRepository(typing.Protocol):
    async def get(self) -> SyncState: ...

    async def save(self, state: SyncState) -> None: ...


def parse_event(raw: dict[str, Any]) -> EventData:
    place = raw["place"]
    return EventData(
        id=raw["id"],
        name=raw["name"],
        place=PlaceData(
            id=place["id"],
            name=place["name"],
            city=place["city"],
            address=place["address"],
            seats_pattern=place.get("seats_pattern"),
        ),
        event_time=datetime.fromisoformat(raw["event_time"]),
        registration_deadline=datetime.fromisoformat(raw["registration_deadline"]),
        status=raw["status"],
        number_of_visitors=raw["number_of_visitors"],
        changed_at=datetime.fromisoformat(raw["changed_at"]),
    )


class SyncEventsUsecase:
    def __init__(
        self,
        events_source: Callable[[str], AsyncIterable[dict[str, Any]]],
        events: EventRepository,
        state: SyncStateRepository,
    ) -> None:
        self._events_source = events_source
        self._events = events
        self._state = state

    async def do(self) -> None:
        state = await self._state.get()
        changed_at_param = (
            state.last_changed_at.date().isoformat()
            if state.last_changed_at
            else FIRST_SYNC_DATE
        )
        await self._state.save(replace(state, sync_status="running"))
        logger.info("Sync started, changed_at=%s", changed_at_param)

        max_changed_at = state.last_changed_at
        batch: list[EventData] = []
        total = 0
        try:
            async for raw in self._events_source(changed_at_param):
                event = parse_event(raw)
                batch.append(event)
                if max_changed_at is None or event.changed_at > max_changed_at:
                    max_changed_at = event.changed_at
                if len(batch) >= BATCH_SIZE:
                    await self._events.upsert_many(batch)
                    total += len(batch)
                    batch = []
            if batch:
                await self._events.upsert_many(batch)
                total += len(batch)
        except Exception as ex:
            logger.exception("Sync failed with exception %s", ex)
            await self._state.save(replace(state, sync_status="failed"))
            raise ex

        await self._state.save(
            SyncState(
                last_sync_time=datetime.now(UTC),
                last_changed_at=max_changed_at,
                sync_status="success",
            )
        )
        logger.info("Sync finished, events processed: %d", total)
