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


@dataclass(frozen=True)
class TicketData:
    id: str
    event_id: str
    first_name: str
    last_name: str
    email: str
    seat: str


class TicketNotFound(Exception):
    pass


class BusinessRuleViolation(Exception):
    """Нарушено бизнес-правило, клиенту уходит 400."""


class EventUnexpectedStatus(BusinessRuleViolation):
    pass


class RegistrationClosed(BusinessRuleViolation):
    pass


class InvalidSeat(BusinessRuleViolation):
    pass


class RequestRejected(BusinessRuleViolation):
    """Провайдер отклонил запрос (400), например место уже занято."""
