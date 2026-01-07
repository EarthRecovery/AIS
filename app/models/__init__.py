from app.db import Base  # re-export Base for Alembic/migrations
# Import models so Alembic autogenerate can see their metadata
from app.models import user, message, history, role, profile  # noqa: F401
