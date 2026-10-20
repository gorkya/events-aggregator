from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain import EventData
from src.models import Event, Place

PLACE_FIELDS = ("name", "city", "address", "seats_pattern")
EVENT_FIELDS = (
    "name",
    "place_id",
    "event_time",
    "registration_deadline",
    "status",
    "number_of_visitors",
    "changed_at",
)


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_many(self, events: list[EventData]) -> None:
        if not events:
            return

        unique_events = {event.id: event for event in events}.values()
        places = {event.place.id: event.place for event in unique_events}.values()

        place_stmt = insert(Place).values(
            [
                {
                    "id": place.id,
                    "name": place.name,
                    "city": place.city,
                    "address": place.address,
                    "seats_pattern": place.seats_pattern,
                }
                for place in places
            ]
        )
        place_stmt = place_stmt.on_conflict_do_update(
            index_elements=[Place.id],
            set_={field: place_stmt.excluded[field] for field in PLACE_FIELDS},
        )
        await self._session.execute(place_stmt)

        event_stmt = insert(Event).values(
            [
                {
                    "id": event.id,
                    "name": event.name,
                    "place_id": event.place.id,
                    "event_time": event.event_time,
                    "registration_deadline": event.registration_deadline,
                    "status": event.status,
                    "number_of_visitors": event.number_of_visitors,
                    "changed_at": event.changed_at,
                }
                for event in unique_events
            ]
        )
        event_stmt = event_stmt.on_conflict_do_update(
            index_elements=[Event.id],
            set_={field: event_stmt.excluded[field] for field in EVENT_FIELDS},
        )
        await self._session.execute(event_stmt)
        await self._session.commit()
