from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class SeatsOut(BaseModel):
    event_id: str
    available_seats: list[str]


class TicketIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_id: str = Field(min_length=1)
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    seat: str = Field(pattern=r"^[A-Z][1-9][0-9]*$")


class TicketOut(BaseModel):
    ticket_id: str


class SuccessOut(BaseModel):
    success: bool
