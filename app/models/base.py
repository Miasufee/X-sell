from sqlalchemy import Column, Integer, TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.ext.declarative import declarative_base

# Base class for declarative models
Base = declarative_base()


class IntIdMixin:
    """Provides an auto-incrementing integer primary key column named 'id'."""
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, index=True)

class TimeStampMixin:
    """Provides automatic timestamping for record creation and updates.
    Uses PostgreSQL's now() function with timezone support.
    """
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        comment="Timestamp when record was created"
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
        comment="Timestamp when record was last updated"
    )