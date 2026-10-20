from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PlaceData:
    id: str
    name: str
    city: str
    address: str
    seats_pattern: str | None


@dataclass(frozen=True)
class EventData:
    id: str
    name: str
    place: PlaceData
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int
    changed_at: datetime


@dataclass(frozen=True)
class SyncState:
    last_sync_time: datetime | None = None
    last_changed_at: datetime | None = None
    sync_status: str = "never"


class EventNotFound(Exception):
    pass


PUBLISHED = "published"


class EventUnexpectedStatus(Exception):
    pass
