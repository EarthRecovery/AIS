from storage.db import Base  # re-export Base for Alembic/migrations
# Import models so Alembic autogenerate can see their metadata
from storage.models import user, message, history, role, profile, summary  # noqa: F401
