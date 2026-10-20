from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    city: str
    address: str


class PlaceDetailOut(PlaceOut):
    seats_pattern: str | None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    place: PlaceOut
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class EventDetailOut(EventOut):
    place: PlaceDetailOut


class EventsListOut(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventOut]
