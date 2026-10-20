import typing

from src.domain import PUBLISHED, EventData, EventNotFound, EventUnexpectedStatus


class SeatsProvider(typing.Protocol):
    async def seats(self, event_id: str) -> list[str]: ...


class EventGetter(typing.Protocol):
    async def get(self, event_id: str) -> EventData | None: ...


class SeatsCache(typing.Protocol):
    def get(self, key: str) -> list[str] | None: ...

    def set(self, key: str, value: list[str]) -> None: ...


class GetSeatsUsecase:
    def __init__(
        self,
        client: SeatsProvider,
        events: EventGetter,
        cache: SeatsCache,
    ) -> None:
        self._client = client
        self._events = events
        self._cache = cache

    async def do(self, event_id: str) -> list[str]:
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFound(event_id)
        if event.status != PUBLISHED:
            raise EventUnexpectedStatus(event.status)

        cached = self._cache.get(event_id)
        if cached is not None:
            return cached

        seats = await self._client.seats(event_id)
        self._cache.set(event_id, seats)
        return seats
