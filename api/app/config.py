import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    session_secret: str
    initial_agent_username: str
    initial_agent_password: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.environ["DATABASE_URL"],
            session_secret=os.environ["SESSION_SECRET"],
            initial_agent_username=os.environ.get("INITIAL_AGENT_USERNAME", ""),
            initial_agent_password=os.environ.get("INITIAL_AGENT_PASSWORD", ""),
        )