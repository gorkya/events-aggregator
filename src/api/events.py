from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.api.deps import (
    get_get_event_usecase,
    get_get_seats_usecase,
    get_list_events_usecase,
)
from src.api.schemas import EventDetailOut, EventOut, EventsListOut, SeatsOut
from src.domain import EventNotFound, EventUnexpectedStatus
from src.usecases.get_events import GetEventUsecase, ListEventsUsecase
from src.usecases.get_seats import GetSeatsUsecase

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventsListOut)
async def list_events(
    request: Request,
    usecase: Annotated[ListEventsUsecase, Depends(get_list_events_usecase)],
    date_from: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> EventsListOut:
    result = await usecase.do(date_from, page, page_size)

    next_url = None
    if page * page_size < result.count:
        next_url = str(request.url.include_query_params(page=page + 1))
    previous_url = None
    if page > 1:
        previous_url = str(request.url.include_query_params(page=page - 1))

    return EventsListOut(
        count=result.count,
        next=next_url,
        previous=previous_url,
        results=[EventOut.model_validate(event) for event in result.items],
    )


@router.get("/{event_id}", response_model=EventDetailOut)
async def get_event(
    event_id: str,
    usecase: Annotated[GetEventUsecase, Depends(get_get_event_usecase)],
) -> EventDetailOut:
    try:
        event = await usecase.do(event_id)
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found") from None
    return EventDetailOut.model_validate(event)


@router.get("/{event_id}/seats", response_model=SeatsOut)
async def get_seats(
    event_id: str,
    usecase: Annotated[GetSeatsUsecase, Depends(get_get_seats_usecase)],
) -> SeatsOut:
    try:
        seats = await usecase.do(event_id)
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found") from None
    except EventUnexpectedStatus:
        raise HTTPException(status_code=400, detail="Event is not published") from None
    return SeatsOut(event_id=event_id, available_seats=seats)
