"""Kafka client utilities."""

from shared.kafka.consumer import KafkaConsumer
from shared.kafka.producer import KafkaProducer

__all__ = ["KafkaConsumer", "KafkaProducer"]
