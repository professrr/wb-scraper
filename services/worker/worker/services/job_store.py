"""In-memory job storage for tracking scrape tasks."""

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from shared.models.job import Job, JobStatus

logger = logging.getLogger(__name__)


class JobStore:
    """Thread-safe in-memory storage for scrape jobs.

    Uses asyncio.Lock for safe concurrent access.
    KISS approach -- no external DB needed for this test assignment.
    """

    def __init__(self) -> None:
        self._jobs: dict[UUID, Job] = {}
        self._lock = asyncio.Lock()

    async def create(self, category_url: str, total_pages: int) -> Job:
        """Create a new job in PENDING state.

        Args:
            category_url: The WB category URL to scrape.
            total_pages: Total number of pages to scrape.

        Returns:
            The newly created Job.
        """
        job = Job(
            id=uuid4(),
            status=JobStatus.PENDING,
            category_url=category_url,
            total_pages=total_pages,
        )
        async with self._lock:
            self._jobs[job.id] = job

        logger.info("Job created: id=%s, url=%s", job.id, category_url)
        return job

    async def get(self, job_id: UUID) -> Job | None:
        """Retrieve a job by its ID.

        Args:
            job_id: UUID of the job.

        Returns:
            The Job if found, otherwise None.
        """
        async with self._lock:
            return self._jobs.get(job_id)

    async def update(self, job_id: UUID, **fields: object) -> Job:
        """Update specific fields of an existing job.

        Args:
            job_id: UUID of the job to update.
            **fields: Field names and values to update.

        Returns:
            The updated Job.

        Raises:
            KeyError: If the job does not exist.
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                msg = f"Job {job_id} not found"
                raise KeyError(msg)

            updated = job.model_copy(update={**fields, "updated_at": datetime.now(UTC)})
            self._jobs[job_id] = updated

        logger.debug("Job updated: id=%s, fields=%s", job_id, list(fields.keys()))
        return updated
