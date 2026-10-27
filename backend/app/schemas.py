"""Request/response models and input validation."""
import re
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

from . import clock

# A donation cannot be scheduled for pickup further ahead than this.
MAX_PICKUP_HORIZON = timedelta(days=7)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?[\d\s\-().]{7,20}$")

DonationStatus = Literal["available", "claimed", "expired"]


class DonationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    food_name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    servings: StrictInt = Field(ge=1, le=100_000)
    location: str = Field(min_length=1, max_length=200)
    pickup_deadline: datetime
    donor_name: str = Field(min_length=1, max_length=120)
    donor_contact: str = Field(min_length=3, max_length=120)
    category: Optional[str] = Field(default=None, max_length=60)

    @field_validator("pickup_deadline")
    @classmethod
    def _check_deadline(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError(
                "pickup_deadline must include a timezone, e.g. 2030-01-01T18:00:00Z"
            )
        value = value.astimezone(timezone.utc)
        now = clock.utcnow()
        if value <= now:
            raise ValueError("pickup_deadline must be in the future")
        if value > now + MAX_PICKUP_HORIZON:
            raise ValueError("pickup_deadline must be within the next 7 days")
        return value

    @field_validator("donor_contact")
    @classmethod
    def _check_contact(cls, value: str) -> str:
        if _EMAIL_RE.match(value):
            return value
        if _PHONE_RE.match(value) and sum(c.isdigit() for c in value) >= 7:
            return value
        raise ValueError("donor_contact must be a valid email address or phone number")

    @field_validator("category")
    @classmethod
    def _blank_category_is_none(cls, value: Optional[str]) -> Optional[str]:
        return value or None


class ClaimRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    claimed_by: str = Field(min_length=1, max_length=120)


class DonationOut(BaseModel):
    """Public representation. Never includes the donor's contact details."""

    id: int
    food_name: str
    description: str
    servings: int
    location: str
    pickup_deadline: datetime
    status: DonationStatus
    donor_name: str
    category: Optional[str] = None
    created_at: datetime
    claimed_by: Optional[str] = None
    claimed_at: Optional[datetime] = None


class ClaimOut(DonationOut):
    """Returned only to whoever successfully claims the donation."""

    donor_contact: str
