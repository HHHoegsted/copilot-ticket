from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Ticket, User

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


class CreateTicketRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)


def ticket_payload(ticket: Ticket) -> dict:
    return {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
        "creator": {"id": ticket.creator_id, "username": ticket.creator.username},
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
    }


def get_visible_ticket(db: Session, ticket_id: int, user: User) -> Ticket:
    """Fetch a ticket, refusing access to customers who do not own it."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or (user.role != "agent" and ticket.creator_id != user.id):
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("", status_code=201)
def create_ticket(
    payload: CreateTicketRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if current_user.role != "customer":
        raise HTTPException(status_code=403, detail="Only customers can create tickets")
    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        status="open",
        creator_id=current_user.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket_payload(ticket)


@router.get("")
def list_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(Ticket)
    if current_user.role == "customer":
        query = query.filter(Ticket.creator_id == current_user.id)
    tickets = query.order_by(Ticket.id.desc()).all()
    return [ticket_payload(ticket) for ticket in tickets]


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    ticket = get_visible_ticket(db, ticket_id, current_user)
    return ticket_payload(ticket)