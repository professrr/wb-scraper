"""Scrape orchestration service -- manages jobs and background scraping tasks."""

import asyncio
import logging
from typing import TYPE_CHECKING

from shared.models.job import Job, JobStatus
from worker.exceptions import KafkaProduceError

if TYPE_CHECKING:
    from uuid import UUID

    from shared.config import KafkaSettings
    from shared.kafka.producer import KafkaProducer
    from worker.clients.categories import CategoriesClient
    from worker.clients.products import ProductsClient
    from worker.config import WorkerSettings
    from worker.services.job_store import JobStore

logger = logging.getLogger(__name__)


class ScrapeService:
    """Orchestrates category scraping: creates jobs, launches background tasks, tracks progress."""

    def __init__(
        self,
        categories_client: CategoriesClient,
        products_client: ProductsClient,
        kafka_producer: KafkaProducer,
        kafka_settings: KafkaSettings,
        job_store: JobStore,
        worker_settings: WorkerSettings,
    ) -> None:
        self._categories = categories_client
        self._products = products_client
        self._kafka = kafka_producer
        self._kafka_settings = kafka_settings
        self._jobs = job_store
        self._settings = worker_settings

    async def start_scrape(self, category_url: str) -> Job:
        """Create a new scrape job and launch the background task.

        Args:
            category_url: Full WB category URL to scrape.

        Returns:
            The newly created Job in PENDING state.
        """
        job = await self._jobs.create(category_url, self._settings.total_pages)
        asyncio.create_task(self._scrape_task(job.id, category_url))  # noqa: RUF006
        logger.info("Scrape started: job_id=%s, url=%s", job.id, category_url)
        return job

    async def get_job(self, job_id: UUID) -> Job | None:
        """Retrieve a job by ID.

        Args:
            job_id: UUID of the job.

        Returns:
            The Job if found, otherwise None.
        """
        return await self._jobs.get(job_id)

    async def _scrape_task(self, job_id: UUID, category_url: str) -> None:
        """Background task: resolve category, fetch pages, produce to Kafka.

        Args:
            job_id: UUID of the job to execute.
            category_url: Full WB category URL.
        """
        try:
            await self._jobs.update(job_id, status=JobStatus.RUNNING)

            tree = await self._categories.fetch_categories()
            search_query = self._categories.resolve_category(category_url, tree)

            for page in range(1, self._settings.total_pages + 1):
                raw_json = await self._products.fetch_page(search_query, page)
                self._produce_to_kafka(raw_json, job_id, page)
                await self._jobs.update(job_id, pages_scraped=page)
                logger.info("Job %s: page %d/%d scraped", job_id, page, self._settings.total_pages)

            await self._jobs.update(job_id, status=JobStatus.COMPLETED)
            logger.info("Job %s completed successfully", job_id)

        except Exception:
            error_msg = f"Scrape failed for job {job_id}"
            logger.exception(error_msg)
            await self._jobs.update(job_id, status=JobStatus.FAILED, error=error_msg)

    def _produce_to_kafka(self, raw_json: str, job_id: UUID, page: int) -> None:
        """Send raw JSON response to Kafka topic.

        Args:
            raw_json: Raw JSON string from WB API.
            job_id: Job UUID used as message key for partitioning.
            page: Page number for logging.

        Raises:
            KafkaProduceError: If the message fails to enqueue.
        """
        topic = self._kafka_settings.category_topic
        try:
            self._kafka.produce(
                topic=topic,
                value=raw_json,
                key=str(job_id),
            )
        except Exception as exc:
            raise KafkaProduceError(topic, str(exc)) from exc
        else:
            logger.debug("Produced page %d to topic '%s' (key=%s)", page, topic, job_id)
