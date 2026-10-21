from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_cancel_ticket_usecase, get_create_ticket_usecase
from src.api.schemas import SuccessOut, TicketIn, TicketOut
from src.domain import BusinessRuleViolation, EventNotFound, TicketNotFound
from src.usecases.tickets import CancelTicketUsecase, CreateTicketUsecase

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", status_code=201, response_model=TicketOut)
async def create_ticket(
    body: TicketIn,
    usecase: Annotated[CreateTicketUsecase, Depends(get_create_ticket_usecase)],
) -> TicketOut:
    try:
        ticket_id = await usecase.do(
            event_id=body.event_id,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            seat=body.seat,
        )
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found") from None
    except BusinessRuleViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return TicketOut(ticket_id=ticket_id)


@router.delete("/{ticket_id}", response_model=SuccessOut)
async def cancel_ticket(
    ticket_id: str,
    usecase: Annotated[CancelTicketUsecase, Depends(get_cancel_ticket_usecase)],
) -> SuccessOut:
    try:
        await usecase.do(ticket_id)
    except TicketNotFound:
        raise HTTPException(status_code=404, detail="Ticket not found") from None
    except BusinessRuleViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return SuccessOut(success=True)
