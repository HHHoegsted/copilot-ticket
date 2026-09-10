from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Session as SessionModel
from app.models import User
from app.security import verify_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    settings = request.app.state.settings
    signed = request.cookies.get("session")
    if not signed:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = verify_token(signed, settings.session_secret)
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = db.query(SessionModel).filter_by(token=token).first()
    if session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user