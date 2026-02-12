"""Kafka configuration with type-safe environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    """Kafka connection and topic settings.

    Reads from environment variables with KAFKA_ prefix.
    Example: KAFKA_BOOTSTRAP_SERVERS=kafka:29092
    """

    model_config = SettingsConfigDict(env_prefix="KAFKA_")

    bootstrap_servers: str = "localhost:9092"
    category_topic: str = "wb-category"
    products_topic: str = "wb-products"
