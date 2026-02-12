"""Kafka consumer wrapper over confluent-kafka."""

import logging
from typing import TYPE_CHECKING

from confluent_kafka import Consumer, KafkaError, KafkaException, Message, TopicPartition

if TYPE_CHECKING:
    from shared.config import KafkaSettings

logger = logging.getLogger(__name__)


class KafkaConsumer:
    """Reusable Kafka consumer with manual offset commit and rebalance logging."""

    def __init__(self, settings: KafkaSettings, group_id: str, topics: list[str]) -> None:
        self._settings = settings
        self._group_id = group_id
        self._consumer = Consumer(
            {
                "bootstrap.servers": settings.bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )
        self._consumer.subscribe(topics, on_assign=self._on_assign, on_revoke=self._on_revoke)
        logger.info(
            "Kafka consumer initialized (servers=%s, group=%s, topics=%s)",
            settings.bootstrap_servers,
            group_id,
            topics,
        )

    @staticmethod
    def _on_assign(consumer: Consumer, partitions: list[TopicPartition]) -> None:
        """Log partition assignments during rebalance."""
        formatted = [f"{p.topic}[{p.partition}]" for p in partitions]
        logger.info("Partitions assigned: %s", formatted)

    @staticmethod
    def _on_revoke(consumer: Consumer, partitions: list[TopicPartition]) -> None:
        """Log partition revocations during rebalance."""
        formatted = [f"{p.topic}[{p.partition}]" for p in partitions]
        logger.info("Partitions revoked: %s", formatted)

    def consume(self, timeout: float = 1.0) -> Message | None:
        """Poll a single message from subscribed topics.

        Args:
            timeout: Maximum time to block waiting for a message in seconds.

        Returns:
            A Message if one is available, or None if the poll timed out.

        Raises:
            KafkaException: On fatal consumer errors.
        """
        msg = self._consumer.poll(timeout)
        if msg is None:
            return None

        error = msg.error()
        if error is not None:
            if error.code() == KafkaError._PARTITION_EOF:  # type: ignore[attr-defined]
                logger.debug(
                    "End of partition %s[%d] at offset %d",
                    msg.topic(),
                    msg.partition(),
                    msg.offset(),
                )
                return None
            logger.error("Consumer error: %s", error)
            raise KafkaException(error)

        return msg

    def commit(self, message: Message) -> None:
        """Synchronously commit the offset for a processed message.

        Args:
            message: The message whose offset to commit.
        """
        self._consumer.commit(message=message, asynchronous=False)
        logger.debug(
            "Offset committed: %s[%d] @ %d",
            message.topic(),
            message.partition(),
            message.offset(),
        )

    def close(self) -> None:
        """Gracefully close the consumer (commit pending offsets and leave group)."""
        logger.info("Closing Kafka consumer (group=%s)...", self._group_id)
        self._consumer.close()
        logger.info("Kafka consumer closed")
