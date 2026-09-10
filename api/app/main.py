from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI

from app.config import Settings
from app.db import init_db
from app.routes.health import router as health_router

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def run_migrations(database_url: str) -> None:
    alembic_config = AlembicConfig(str(ALEMBIC_INI))
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    init_db(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        run_migrations(settings.database_url)
        yield

    app = FastAPI(title="Ticketing API", lifespan=lifespan)
    app.include_router(health_router)
    return app


app = create_app()