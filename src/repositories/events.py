from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain import EventData, PlaceData
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


def _start_of_day(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def _to_data(model: Event) -> EventData:
    place = model.place
    return EventData(
        id=model.id,
        name=model.name,
        place=PlaceData(
            id=place.id,
            name=place.name,
            city=place.city,
            address=place.address,
            seats_pattern=place.seats_pattern,
        ),
        event_time=model.event_time,
        registration_deadline=model.registration_deadline,
        status=model.status,
        number_of_visitors=model.number_of_visitors,
        changed_at=model.changed_at,
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

    async def count(self, date_from: date | None = None) -> int:
        stmt = select(func.count()).select_from(Event)
        if date_from is not None:
            stmt = stmt.where(Event.event_time >= _start_of_day(date_from))
        return await self._session.scalar(stmt) or 0

    async def get_many(
        self, date_from: date | None, limit: int, offset: int
    ) -> list[EventData]:
        stmt = select(Event).order_by(Event.event_time, Event.id)
        if date_from is not None:
            stmt = stmt.where(Event.event_time >= _start_of_day(date_from))
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.scalars(stmt)
        return [_to_data(event) for event in result]

    async def get(self, event_id: str) -> EventData | None:
        event = await self._session.get(Event, event_id)
        return _to_data(event) if event else None
