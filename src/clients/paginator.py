from collections.abc import AsyncIterator
from typing import Any

from src.clients.events_provider import EventsProviderClient


class EventsPaginator:
    def __init__(
        self,
        client: EventsProviderClient,
        changed_at: str = "2000-01-01",
    ) -> None:
        self._client = client
        self._changed_at = changed_at

    def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[dict[str, Any]]:
        cursor = None
        while True:
            page = await self._client.events(self._changed_at, cursor)
            for event in page.results:
                yield event
            if page.next_cursor is None:
                break
            cursor = page.next_cursor
