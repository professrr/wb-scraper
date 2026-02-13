"""API router with scrape endpoints."""

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003 -- FastAPI needs UUID at runtime for path param parsing

from fastapi import APIRouter, HTTPException, Request, status

from worker.api.schemas import JobStatusResponse, ScrapeRequest, ScrapeResponse

if TYPE_CHECKING:
    from worker.services.scrape_service import ScrapeService

router = APIRouter(prefix="/api/v1/scrape", tags=["scrape"])


def _get_scrape_service(request: Request) -> ScrapeService:
    """Extract ScrapeService from app state."""
    service: ScrapeService = request.app.state.scrape_service
    return service


@router.post(
    "",
    response_model=ScrapeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start category scraping",
    description="Accepts a WB category URL and launches a background scrape task.",
)
async def start_scrape(body: ScrapeRequest, request: Request) -> ScrapeResponse:
    """Start scraping a WB category. Returns job ID for status tracking."""
    service = _get_scrape_service(request)
    job = await service.start_scrape(str(body.category_url))
    return ScrapeResponse(job_id=job.id, status=job.status)


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get scrape job status",
    description="Returns the current status and progress of a scrape job.",
)
async def get_job_status(job_id: UUID, request: Request) -> JobStatusResponse:
    """Get the current status of a scrape job."""
    service = _get_scrape_service(request)
    job = await service.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        category_url=job.category_url,
        pages_scraped=job.pages_scraped,
        total_pages=job.total_pages,
        error=job.error,
        error_reason=job.error_reason,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
