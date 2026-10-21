from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain import TicketData
from src.models import Ticket


class TicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, ticket: TicketData) -> None:
        values = {
            "event_id": ticket.event_id,
            "first_name": ticket.first_name,
            "last_name": ticket.last_name,
            "email": ticket.email,
            "seat": ticket.seat,
        }
        stmt = insert(Ticket).values(id=ticket.id, **values)
        stmt = stmt.on_conflict_do_update(index_elements=[Ticket.id], set_=values)
        await self._session.execute(stmt)
        await self._session.commit()

    async def get(self, ticket_id: str) -> TicketData | None:
        row = await self._session.get(Ticket, ticket_id)
        if row is None:
            return None
        return TicketData(
            id=row.id,
            event_id=row.event_id,
            first_name=row.first_name,
            last_name=row.last_name,
            email=row.email,
            seat=row.seat,
        )

    async def delete(self, ticket_id: str) -> None:
        await self._session.execute(delete(Ticket).where(Ticket.id == ticket_id))
        await self._session.commit()
