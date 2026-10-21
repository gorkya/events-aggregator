from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain import (
    EventNotFound,
    EventUnexpectedStatus,
    InvalidSeat,
    RegistrationClosed,
    RequestRejected,
    TicketData,
    TicketNotFound,
)
from src.usecases.tickets import CancelTicketUsecase, CreateTicketUsecase
from tests.factories import make_event

BEFORE_DEADLINE = datetime.fromisoformat("2026-01-01T00:00:00+03:00")
AFTER_DEADLINE = datetime.fromisoformat("2026-01-10T18:00:00+03:00")


def make_create(event, now=BEFORE_DEADLINE):
    client = MagicMock()
    client.register = AsyncMock(return_value="t1")
    events = MagicMock()
    events.get = AsyncMock(return_value=event)
    tickets = MagicMock()
    tickets.create = AsyncMock()
    cache = MagicMock()
    usecase = CreateTicketUsecase(client, events, tickets, cache, clock=lambda: now)
    return usecase, client, tickets, cache


async def create(usecase, seat="A5"):
    return await usecase.do("e1", "Ivan", "Ivanov", "ivan@example.com", seat)


@pytest.mark.anyio
async def test_create_ticket_success():
    usecase, client, tickets, cache = make_create(make_event("e1"))

    ticket_id = await create(usecase)

    assert ticket_id == "t1"
    client.register.assert_awaited_once_with(
        "e1", "Ivan", "Ivanov", "ivan@example.com", "A5"
    )
    tickets.create.assert_awaited_once_with(
        TicketData(
            id="t1",
            event_id="e1",
            first_name="Ivan",
            last_name="Ivanov",
            email="ivan@example.com",
            seat="A5",
        )
    )
    cache.delete.assert_called_once_with("e1")


@pytest.mark.anyio
async def test_create_ticket_event_not_found():
    usecase, client, _, _ = make_create(None)

    with pytest.raises(EventNotFound):
        await create(usecase)

    client.register.assert_not_awaited()


@pytest.mark.anyio
async def test_create_ticket_event_not_published():
    usecase, client, _, _ = make_create(make_event("e1", status="new"))

    with pytest.raises(EventUnexpectedStatus):
        await create(usecase)

    client.register.assert_not_awaited()


@pytest.mark.anyio
async def test_create_ticket_after_deadline():
    usecase, client, _, _ = make_create(make_event("e1"), now=AFTER_DEADLINE)

    with pytest.raises(RegistrationClosed):
        await create(usecase)

    client.register.assert_not_awaited()


@pytest.mark.anyio
async def test_create_ticket_invalid_seat():
    usecase, client, _, _ = make_create(make_event("e1"))

    with pytest.raises(InvalidSeat):
        await create(usecase, seat="A11")

    client.register.assert_not_awaited()


@pytest.mark.anyio
async def test_create_ticket_provider_rejects_and_nothing_saved():
    usecase, client, tickets, cache = make_create(make_event("e1"))
    client.register.side_effect = RequestRejected("already sold")

    with pytest.raises(RequestRejected):
        await create(usecase)

    tickets.create.assert_not_awaited()
    cache.delete.assert_not_called()


def make_cancel(ticket):
    client = MagicMock()
    client.unregister = AsyncMock()
    tickets = MagicMock()
    tickets.get = AsyncMock(return_value=ticket)
    tickets.delete = AsyncMock()
    cache = MagicMock()
    return CancelTicketUsecase(client, tickets, cache), client, tickets, cache


def make_ticket() -> TicketData:
    return TicketData(
        id="t1",
        event_id="e1",
        first_name="Ivan",
        last_name="Ivanov",
        email="ivan@example.com",
        seat="A5",
    )


@pytest.mark.anyio
async def test_cancel_ticket_success():
    usecase, client, tickets, cache = make_cancel(make_ticket())

    await usecase.do("t1")

    client.unregister.assert_awaited_once_with("e1", "t1")
    tickets.delete.assert_awaited_once_with("t1")
    cache.delete.assert_called_once_with("e1")


@pytest.mark.anyio
async def test_cancel_ticket_not_found():
    usecase, client, _, _ = make_cancel(None)

    with pytest.raises(TicketNotFound):
        await usecase.do("missing")

    client.unregister.assert_not_awaited()


@pytest.mark.anyio
async def test_cancel_ticket_provider_rejects_keeps_ticket():
    usecase, client, tickets, _ = make_cancel(make_ticket())
    client.unregister.side_effect = RequestRejected("event is in the past")

    with pytest.raises(RequestRejected):
        await usecase.do("t1")

    tickets.delete.assert_not_awaited()
