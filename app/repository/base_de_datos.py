"""Single source of the database engine (D-011).

The URL comes only from ``DATABASE_URL`` in ``.env``. There is deliberately no
fallback: a missing variable must stop the app with a clear message instead of
silently connecting to some other database.

No session is kept at module level: every caller opens and closes its own.
"""

import os

from dotenv import load_dotenv
from sqlmodel import Session, create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill in the "
        "database credentials (D-011)."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


def get_session() -> Session:
    """Return a new session; the caller owns its lifecycle."""
    return Session(engine)


def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
