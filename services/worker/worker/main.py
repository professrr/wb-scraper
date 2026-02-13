"""FastAPI application entrypoint with lifespan management and error handling."""

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from curl_cffi.requests import AsyncSession
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.config import KafkaSettings
from shared.kafka.producer import KafkaProducer
from worker.api.router import router
from worker.clients.categories import CategoriesClient
from worker.clients.products import ProductsClient
from worker.config import WorkerSettings
from worker.exceptions import CategoryNotFoundError, CategoryNotScrappableError, KafkaProduceError, WBApiError
from worker.services.job_store import JobStore
from worker.services.scrape_service import ScrapeService

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle: initialize and tear down resources."""
    worker_settings = WorkerSettings()
    kafka_settings = KafkaSettings()

    kafka_producer = KafkaProducer(kafka_settings)

    session = AsyncSession(impersonate="safari")

    categories_client = CategoriesClient(session, worker_settings.wb_base_url)
    products_client = ProductsClient(session, worker_settings.wb_base_url)
    job_store = JobStore()

    scrape_service = ScrapeService(
        categories_client=categories_client,
        products_client=products_client,
        kafka_producer=kafka_producer,
        kafka_settings=kafka_settings,
        job_store=job_store,
        worker_settings=worker_settings,
    )

    app.state.scrape_service = scrape_service
    logger.info("Worker service started (host=%s, port=%d)", worker_settings.host, worker_settings.port)

    yield

    kafka_producer.flush()
    await session.close()
    logger.info("Worker service shut down gracefully")


app = FastAPI(
    title="WB Scraper Worker",
    version="1.1.0",
    description="REST API for scraping Wildberries product categories via mobile API",
    lifespan=lifespan,
)
app.include_router(router)


@app.exception_handler(CategoryNotFoundError)
async def category_not_found_handler(_request: Request, exc: CategoryNotFoundError) -> JSONResponse:
    """Handle category resolution failures."""
    logger.warning("Category not found: %s", exc.url_path)
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


@app.exception_handler(CategoryNotScrappableError)
async def category_not_scrappable_handler(_request: Request, exc: CategoryNotScrappableError) -> JSONResponse:
    """Handle attempts to scrape a category that has no searchQuery."""
    logger.warning("Category not scrappable: %s (%s)", exc.node_name, exc.url_path)
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


@app.exception_handler(WBApiError)
async def wb_api_error_handler(_request: Request, exc: WBApiError) -> JSONResponse:
    """Handle WB API communication errors."""
    logger.error("WB API error: %s", exc)
    return JSONResponse(
        status_code=502,
        content={"detail": str(exc)},
    )


@app.exception_handler(KafkaProduceError)
async def kafka_produce_error_handler(_request: Request, exc: KafkaProduceError) -> JSONResponse:
    """Handle Kafka production failures."""
    logger.error("Kafka produce error: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors with a generic 500 response."""
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
