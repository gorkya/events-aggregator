import typing
from dataclasses import dataclass
from datetime import date

from src.domain import EventData, EventNotFound


class EventReader(typing.Protocol):
    async def count(self, date_from: date | None) -> int: ...

    async def get_many(
        self, date_from: date | None, limit: int, offset: int
    ) -> list[EventData]: ...

    async def get(self, event_id: str) -> EventData | None: ...


@dataclass(frozen=True)
class EventsList:
    count: int
    items: list[EventData]


class ListEventsUsecase:
    def __init__(self, events: EventReader) -> None:
        self._events = events

    async def do(self, date_from: date | None, page: int, page_size: int) -> EventsList:
        offset = (page - 1) * page_size
        count = await self._events.count(date_from)
        items = await self._events.get_many(date_from, limit=page_size, offset=offset)
        return EventsList(count=count, items=items)


class GetEventUsecase:
    def __init__(self, events: EventReader) -> None:
        self._events = events

    async def do(self, event_id: str) -> EventData:
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFound(event_id)
        return event
