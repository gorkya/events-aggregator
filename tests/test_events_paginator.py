from unittest.mock import AsyncMock, MagicMock, call

import pytest

from src.clients.events_provider import EventsPage
from src.clients.paginator import EventsPaginator


@pytest.mark.anyio
async def test_paginator_iterates_all_pages():
    client = MagicMock()
    client.events = AsyncMock(
        side_effect=[
            EventsPage(results=[{"id": "1"}, {"id": "2"}], next_cursor="abc"),
            EventsPage(results=[{"id": "3"}], next_cursor=None),
        ]
    )

    events = [event async for event in EventsPaginator(client)]

    assert [event["id"] for event in events] == ["1", "2", "3"]
    assert client.events.await_args_list == [
        call("2000-01-01", None),
        call("2000-01-01", "abc"),
    ]


@pytest.mark.anyio
async def test_paginator_empty_result():
    client = MagicMock()
    client.events = AsyncMock(return_value=EventsPage(results=[], next_cursor=None))

    events = [event async for event in EventsPaginator(client)]

    assert events == []
    client.events.assert_awaited_once_with("2000-01-01", None)


@pytest.mark.anyio
async def test_paginator_uses_changed_at():
    client = MagicMock()
    client.events = AsyncMock(return_value=EventsPage(results=[], next_cursor=None))

    _ = [e async for e in EventsPaginator(client, changed_at="2026-01-01")]

    client.events.assert_awaited_once_with("2026-01-01", None)
