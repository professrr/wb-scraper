"""Worker service configuration with type-safe environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    """Worker service settings.

    Reads from environment variables with WORKER_ prefix.
    Example: WORKER_TOTAL_PAGES=5
    """

    model_config = SettingsConfigDict(env_prefix="WORKER_")

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000
    total_pages: int = 5
    wb_base_url: str = "https://api-ios.wildberries.ru"
