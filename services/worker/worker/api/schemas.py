"""Pydantic request/response schemas for the worker API."""

from datetime import datetime  # noqa: TC003 -- Pydantic needs datetime at runtime
from uuid import UUID  # noqa: TC003 -- Pydantic needs UUID at runtime

from pydantic import BaseModel, HttpUrl, field_validator

from shared.models.job import JobStatus  # noqa: TC001 -- Pydantic needs JobStatus at runtime

_ALLOWED_HOSTS = {"www.wildberries.ru", "wildberries.ru"}


class ScrapeRequest(BaseModel):
    """Request body for POST /api/v1/scrape."""

    category_url: HttpUrl

    @field_validator("category_url")
    @classmethod
    def validate_wildberries_domain(cls, v: HttpUrl) -> HttpUrl:
        """Ensure the URL belongs to wildberries.ru domain."""
        if v.host not in _ALLOWED_HOSTS:
            msg = f"URL must be a wildberries.ru domain, got '{v.host}'"
            raise ValueError(msg)
        return v


class ScrapeResponse(BaseModel):
    """Response for POST /api/v1/scrape (202 Accepted)."""

    job_id: UUID
    status: JobStatus


class JobStatusResponse(BaseModel):
    """Response for GET /api/v1/scrape/{job_id}."""

    job_id: UUID
    status: JobStatus
    category_url: str
    pages_scraped: int
    total_pages: int
    error: str | None
    created_at: datetime
    updated_at: datetime
