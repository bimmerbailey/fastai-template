from pydantic import AwareDatetime
from sqlmodel import DateTime, Field, SQLModel, func

from fastai.utils.fields import date_now


class TimestampMixin(SQLModel):
    """Shared timestamp fields for all database table models.

    Provides created_at and updated_at with timezone-aware UTC datetimes.
    Only use as a parent class for table models (table=True).
    """

    created_at: AwareDatetime = Field(
        default_factory=date_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "nullable": False},
    )
    updated_at: AwareDatetime = Field(
        default_factory=date_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now(),
            "nullable": False,
        },
    )
