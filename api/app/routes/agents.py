from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("")
def list_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    if current_user.role != "agent":
        raise HTTPException(status_code=403, detail="Only agents can view the agent list")
    agents = db.query(User).filter(User.role == "agent").order_by(User.id).all()
    return [{"id": agent.id, "username": agent.username} for agent in agents]