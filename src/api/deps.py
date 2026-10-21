from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.events_provider import EventsProviderClient
from src.core.cache import TTLCache
from src.core.db import session_factory
from src.repositories.events import EventRepository
from src.repositories.tickets import TicketRepository
from src.usecases.get_events import GetEventUsecase, ListEventsUsecase
from src.usecases.get_seats import GetSeatsUsecase
from src.usecases.tickets import CancelTicketUsecase, CreateTicketUsecase


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_events_client(request: Request) -> EventsProviderClient:
    return request.app.state.events_client


def get_seats_cache(request: Request) -> TTLCache[list[str]]:
    return request.app.state.seats_cache


def get_list_events_usecase(session: SessionDep) -> ListEventsUsecase:
    return ListEventsUsecase(EventRepository(session))


def get_get_event_usecase(session: SessionDep) -> GetEventUsecase:
    return GetEventUsecase(EventRepository(session))


def get_get_seats_usecase(
    session: SessionDep,
    client: Annotated[EventsProviderClient, Depends(get_events_client)],
    cache: Annotated[TTLCache[list[str]], Depends(get_seats_cache)],
) -> GetSeatsUsecase:
    return GetSeatsUsecase(client, EventRepository(session), cache)


def get_create_ticket_usecase(
    session: SessionDep,
    client: Annotated[EventsProviderClient, Depends(get_events_client)],
    cache: Annotated[TTLCache[list[str]], Depends(get_seats_cache)],
) -> CreateTicketUsecase:
    return CreateTicketUsecase(
        client, EventRepository(session), TicketRepository(session), cache
    )


def get_cancel_ticket_usecase(
    session: SessionDep,
    client: Annotated[EventsProviderClient, Depends(get_events_client)],
    cache: Annotated[TTLCache[list[str]], Depends(get_seats_cache)],
) -> CancelTicketUsecase:
    return CancelTicketUsecase(client, TicketRepository(session), cache)
