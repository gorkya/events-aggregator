from datetime import datetime

from src.domain import EventData, PlaceData


def make_event(event_id: str = "e1", status: str = "published") -> EventData:
    return EventData(
        id=event_id,
        name="Event",
        place=PlaceData(
            id="p1",
            name="Place",
            city="City",
            address="Address",
            seats_pattern="A1-10",
        ),
        event_time=datetime.fromisoformat("2026-01-11T17:00:00+03:00"),
        registration_deadline=datetime.fromisoformat("2026-01-10T17:00:00+03:00"),
        status=status,
        number_of_visitors=5,
        changed_at=datetime.fromisoformat("2026-01-04T22:28:35+03:00"),
    )
