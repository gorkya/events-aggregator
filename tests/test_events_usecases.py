from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain import EventNotFound
from src.usecases.get_events import GetEventUsecase, ListEventsUsecase
from tests.factories import make_event


@pytest.mark.anyio
async def test_list_events_calculates_offset():
    repo = MagicMock()
    repo.count = AsyncMock(return_value=45)
    repo.get_many = AsyncMock(return_value=[make_event()])

    result = await ListEventsUsecase(repo).do(date(2026, 1, 1), page=3, page_size=20)

    assert result.count == 45
    assert len(result.items) == 1
    repo.count.assert_awaited_once_with(date(2026, 1, 1))
    repo.get_many.assert_awaited_once_with(date(2026, 1, 1), limit=20, offset=40)


@pytest.mark.anyio
async def test_get_event_returns_event():
    repo = MagicMock()
    repo.get = AsyncMock(return_value=make_event("e1"))

    event = await GetEventUsecase(repo).do("e1")

    assert event.id == "e1"


@pytest.mark.anyio
async def test_get_event_not_found():
    repo = MagicMock()
    repo.get = AsyncMock(return_value=None)

    with pytest.raises(EventNotFound):
        await GetEventUsecase(repo).do("missing")
