"""Parser service entrypoint: Kafka consumer loop that parses WB product data."""

import logging
import signal
import sys
from typing import TYPE_CHECKING

from confluent_kafka import KafkaException

from parser.config import ParserSettings
from parser.product_parser import parse_products
from shared.config import KafkaSettings
from shared.kafka.consumer import KafkaConsumer
from shared.kafka.producer import KafkaProducer

if TYPE_CHECKING:
    from types import FrameType

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_shutdown = False


def _handle_signal(signum: int, _frame: FrameType | None) -> None:
    """Set shutdown flag on SIGTERM/SIGINT for graceful exit."""
    global _shutdown
    sig_name = signal.Signals(signum).name
    logger.info("Received %s, shutting down...", sig_name)
    _shutdown = True


def main() -> None:
    """Run the parser consume loop: read from wb-category, parse, produce to wb-products."""
    kafka_settings = KafkaSettings()
    parser_settings = ParserSettings()

    consumer = KafkaConsumer(
        settings=kafka_settings,
        group_id=parser_settings.consumer_group,
        topics=[kafka_settings.category_topic],
    )
    producer = KafkaProducer(kafka_settings)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info(
        "Parser started (group=%s, source=%s, target=%s)",
        parser_settings.consumer_group,
        kafka_settings.category_topic,
        kafka_settings.products_topic,
    )

    try:
        while not _shutdown:
            msg = consumer.consume(timeout=parser_settings.poll_timeout)
            if msg is None:
                continue

            raw_value = msg.value()
            if raw_value is None:
                logger.warning("Received message with empty value, skipping")
                consumer.commit(msg)
                continue

            try:
                products = parse_products(raw_value.decode("utf-8"))
            except Exception:
                logger.exception("Failed to parse message, skipping")
                consumer.commit(msg)
                continue

            try:
                for product in products:
                    producer.produce(
                        topic=kafka_settings.products_topic,
                        value=product.model_dump_json(),
                    )
            except KafkaException:
                logger.exception("Failed to produce products, will NOT commit offset")
                continue

            consumer.commit(msg)
            logger.debug("Message processed: %d products produced", len(products))

    except Exception:
        logger.exception("Fatal error in consume loop")
        sys.exit(1)
    finally:
        logger.info("Shutting down parser...")
        consumer.close()
        producer.flush()
        logger.info("Parser shut down gracefully")


if __name__ == "__main__":
    main()
