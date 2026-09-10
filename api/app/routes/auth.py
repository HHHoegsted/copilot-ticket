from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Session as SessionModel
from app.models import User
from app.security import (
    generate_token,
    hash_password,
    sign_token,
    verify_password,
    verify_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

SESSION_COOKIE = "session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days; the server-side row is deleted on logout


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


def user_payload(user: User) -> dict:
    return {"id": user.id, "username": user.username, "role": user.role}


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    existing = db.query(User).filter_by(username=payload.username).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Username is already taken")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role="customer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_payload(user)


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    user = db.query(User).filter_by(username=payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = generate_token()
    db.add(SessionModel(token=token, user_id=user.id))
    db.commit()
    response.set_cookie(
        SESSION_COOKIE,
        sign_token(token, request.app.state.settings.session_secret),
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
    )
    return user_payload(user)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    signed = request.cookies.get(SESSION_COOKIE)
    if signed:
        token = verify_token(signed, request.app.state.settings.session_secret)
        if token is not None:
            db.query(SessionModel).filter_by(token=token).delete()
            db.commit()
    response.delete_cookie(SESSION_COOKIE)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> dict:
    return user_payload(current_user)