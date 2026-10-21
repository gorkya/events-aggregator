import typing
from collections.abc import Callable
from datetime import UTC, datetime

from src.domain import (
    PUBLISHED,
    EventData,
    EventNotFound,
    EventUnexpectedStatus,
    InvalidSeat,
    RegistrationClosed,
    TicketData,
    TicketNotFound,
)
from src.usecases.seat_pattern import seat_in_pattern


class ProviderTickets(typing.Protocol):
    async def register(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str: ...

    async def unregister(self, event_id: str, ticket_id: str) -> None: ...


class EventGetter(typing.Protocol):
    async def get(self, event_id: str) -> EventData | None: ...


class TicketStore(typing.Protocol):
    async def create(self, ticket: TicketData) -> None: ...

    async def get(self, ticket_id: str) -> TicketData | None: ...

    async def delete(self, ticket_id: str) -> None: ...


class SeatsCacheInvalidator(typing.Protocol):
    def delete(self, key: str) -> None: ...


def _utcnow() -> datetime:
    return datetime.now(UTC)


class CreateTicketUsecase:
    def __init__(
        self,
        client: ProviderTickets,
        events: EventGetter,
        tickets: TicketStore,
        cache: SeatsCacheInvalidator,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets
        self._cache = cache
        self._clock = clock

    async def do(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str:
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFound(event_id)
        if event.status != PUBLISHED:
            raise EventUnexpectedStatus("Event is not published")
        if self._clock() >= event.registration_deadline:
            raise RegistrationClosed("Registration deadline has passed")
        pattern = event.place.seats_pattern
        if pattern and not seat_in_pattern(pattern, seat):
            raise InvalidSeat(f"Seat {seat} does not exist for this event")

        ticket_id = await self._client.register(
            event.id, first_name, last_name, email, seat
        )
        self._cache.delete(event.id)
        await self._tickets.create(
            TicketData(
                id=ticket_id,
                event_id=event.id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                seat=seat,
            )
        )
        return ticket_id


class CancelTicketUsecase:
    def __init__(
        self,
        client: ProviderTickets,
        tickets: TicketStore,
        cache: SeatsCacheInvalidator,
    ) -> None:
        self._client = client
        self._tickets = tickets
        self._cache = cache

    async def do(self, ticket_id: str) -> None:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise TicketNotFound(ticket_id)

        await self._client.unregister(ticket.event_id, ticket.id)
        self._cache.delete(ticket.event_id)
        await self._tickets.delete(ticket.id)
