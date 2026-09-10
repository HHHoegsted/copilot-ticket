from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Reply, Ticket, User

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


class CreateTicketRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)


class CreateReplyRequest(BaseModel):
    body: str = Field(min_length=1)


class AssignTicketRequest(BaseModel):
    assignee_id: int


def reply_payload(reply: Reply) -> dict:
    return {
        "id": reply.id,
        "author": {"id": reply.author_id, "username": reply.author.username},
        "body": reply.body,
        "created_at": reply.created_at.isoformat(),
    }


def ticket_payload(ticket: Ticket, include_replies: bool = False) -> dict:
    payload = {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
        "creator": {"id": ticket.creator_id, "username": ticket.creator.username},
        "assignee": (
            {"id": ticket.assignee_id, "username": ticket.assignee.username}
            if ticket.assignee
            else None
        ),
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
    }
    if include_replies:
        payload["replies"] = [reply_payload(r) for r in ticket.replies]
    return payload


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
    return ticket_payload(ticket, include_replies=True)


@router.put("/{ticket_id}/assignee")
def assign_ticket(
    ticket_id: int,
    payload: AssignTicketRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if current_user.role != "agent":
        raise HTTPException(status_code=403, detail="Only agents can assign tickets")
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    assignee = db.get(User, payload.assignee_id)
    if assignee is None:
        raise HTTPException(status_code=404, detail="Assignee not found")
    if assignee.role != "agent":
        raise HTTPException(status_code=422, detail="Assignee must be an agent")
    ticket.assignee_id = assignee.id
    db.commit()
    db.refresh(ticket)
    return ticket_payload(ticket)


@router.post("/{ticket_id}/replies", status_code=201)
def create_reply(
    ticket_id: int,
    payload: CreateReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    ticket = get_visible_ticket(db, ticket_id, current_user)
    reply = Reply(ticket_id=ticket.id, author_id=current_user.id, body=payload.body)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply_payload(reply)