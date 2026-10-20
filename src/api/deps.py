from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import session_factory
from src.repositories.events import EventRepository
from src.usecases.get_events import GetEventUsecase, ListEventsUsecase


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_list_events_usecase(session: SessionDep) -> ListEventsUsecase:
    return ListEventsUsecase(EventRepository(session))


def get_get_event_usecase(session: SessionDep) -> GetEventUsecase:
    return GetEventUsecase(EventRepository(session))
