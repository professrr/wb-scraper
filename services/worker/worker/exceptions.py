"""Custom exceptions for the worker service."""


class CategoryNotFoundError(Exception):
    """Raised when a category cannot be resolved from the WB category tree."""

    def __init__(self, url_path: str) -> None:
        self.url_path = url_path
        super().__init__(f"Category not found for path: {url_path}")


class WBApiError(Exception):
    """Raised when the Wildberries mobile API returns an unexpected response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"WB API error (HTTP {status_code}): {message}")


class KafkaProduceError(Exception):
    """Raised when a message cannot be sent to Kafka."""

    def __init__(self, topic: str, detail: str) -> None:
        self.topic = topic
        self.detail = detail
        super().__init__(f"Failed to produce to topic '{topic}': {detail}")
