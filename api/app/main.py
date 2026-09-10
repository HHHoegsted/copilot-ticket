from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI

from app import db
from app.config import Settings
from app.models import User
from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.security import hash_password

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def run_migrations(database_url: str) -> None:
    alembic_config = AlembicConfig(str(ALEMBIC_INI))
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")


def seed_initial_agent(settings: Settings) -> None:
    """Create the initial agent from environment variables if it does not exist.

    Idempotent: on later starts the existing agent is left untouched.
    """
    if not settings.initial_agent_username:
        return
    assert db.SessionLocal is not None  # set by init_db in create_app
    with db.SessionLocal() as session:
        existing = session.query(User).filter_by(username=settings.initial_agent_username).first()
        if existing is None:
            session.add(
                User(
                    username=settings.initial_agent_username,
                    password_hash=hash_password(settings.initial_agent_password),
                    role="agent",
                )
            )
            session.commit()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    db.init_db(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        run_migrations(settings.database_url)
        seed_initial_agent(settings)
        yield

    app = FastAPI(title="Ticketing API", lifespan=lifespan)
    app.state.settings = settings
    app.include_router(health_router)
    app.include_router(auth_router)
    return app


app = create_app()