"""Kafka producer wrapper over confluent-kafka."""

import logging
from typing import TYPE_CHECKING, Any

from confluent_kafka import KafkaError, KafkaException, Producer

if TYPE_CHECKING:
    from shared.config import KafkaSettings

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Thread-safe Kafka producer with JSON serialization and delivery tracking."""

    def __init__(self, settings: KafkaSettings) -> None:
        self._settings = settings
        self._producer = Producer(
            {
                "bootstrap.servers": settings.bootstrap_servers,
                "client.id": "wb-scraper-producer",
                "acks": "all",
            }
        )
        logger.info("Kafka producer initialized (servers=%s)", settings.bootstrap_servers)

    @staticmethod
    def _delivery_callback(err: KafkaError | None, msg: Any) -> None:
        """Log delivery result for each produced message."""
        if err is not None:
            logger.error("Message delivery failed: %s", err)
        else:
            logger.debug(
                "Message delivered to %s [partition=%s, offset=%s]",
                msg.topic(),
                msg.partition(),
                msg.offset(),
            )

    def produce(self, topic: str, value: str, key: str | None = None) -> None:
        """Produce a JSON string message to the given Kafka topic.

        Args:
            topic: Target Kafka topic name.
            value: Raw JSON string to send as message value.
            key: Optional message key for partitioning.

        Raises:
            KafkaException: If the message cannot be enqueued.
        """
        try:
            self._producer.produce(
                topic=topic,
                value=value.encode("utf-8"),
                key=key.encode("utf-8") if key else None,
                callback=self._delivery_callback,
            )
            self._producer.poll(0)
        except KafkaException:
            logger.exception("Failed to produce message to topic %s", topic)
            raise

    def flush(self, timeout: float = 10.0) -> int:
        """Flush all buffered messages, blocking until delivery or timeout.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            Number of messages still in the queue (0 means all delivered).
        """
        remaining: int = self._producer.flush(timeout)
        if remaining > 0:
            logger.warning("Kafka flush timeout: %d messages still in queue", remaining)
        return remaining

    def poll(self, timeout: float = 0) -> int:
        """Poll for delivery callbacks.

        Args:
            timeout: Maximum time to block in seconds.

        Returns:
            Number of callbacks served.
        """
        return self._producer.poll(timeout)
