"""Job domain model for tracking scrape tasks."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID  # noqa: TC003 -- Pydantic needs UUID at runtime

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    """Possible states of a scrape job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """Represents a single scrape job with its current state."""

    id: UUID
    status: JobStatus = JobStatus.PENDING
    category_url: str
    pages_scraped: int = 0
    total_pages: int = 5
    error: str | None = None
    error_reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
