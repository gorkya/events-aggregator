from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain import EventNotFound, EventUnexpectedStatus
from src.usecases.get_seats import GetSeatsUsecase
from tests.factories import make_event


def make_usecase(event, cached=None):
    client = MagicMock()
    client.seats = AsyncMock(return_value=["A1", "A2"])
    events = MagicMock()
    events.get = AsyncMock(return_value=event)
    cache = MagicMock()
    cache.get = MagicMock(return_value=cached)
    cache.set = MagicMock()
    return GetSeatsUsecase(client, events, cache), client, cache


@pytest.mark.anyio
async def test_returns_seats_and_caches_them():
    usecase, client, cache = make_usecase(make_event("e1"))

    seats = await usecase.do("e1")

    assert seats == ["A1", "A2"]
    client.seats.assert_awaited_once_with("e1")
    cache.set.assert_called_once_with("e1", ["A1", "A2"])


@pytest.mark.anyio
async def test_returns_cached_seats_without_calling_provider():
    usecase, client, cache = make_usecase(make_event("e1"), cached=["B1"])

    seats = await usecase.do("e1")

    assert seats == ["B1"]
    client.seats.assert_not_awaited()


@pytest.mark.anyio
async def test_event_not_found():
    usecase, client, _ = make_usecase(None)

    with pytest.raises(EventNotFound):
        await usecase.do("missing")

    client.seats.assert_not_awaited()


@pytest.mark.anyio
async def test_unpublished_event_does_not_call_provider():
    usecase, client, _ = make_usecase(make_event("e1", status="new"))

    with pytest.raises(EventUnexpectedStatus):
        await usecase.do("e1")

    client.seats.assert_not_awaited()
