"""Pydantic models for parsed Wildberries product data."""

from datetime import datetime  # noqa: TC003 - Pydantic needs this at runtime

from pydantic import BaseModel


class ParsedProduct(BaseModel):
    """A single parsed product ready for producing to the wb-products topic.

    Attributes:
        received_at: Timestamp when the raw data was received and parsed.
        product_id: Wildberries product identifier.
        name: Product display name.
        price: Product price in rubles (converted from kopecks).
        discount: Discount percentage (0-100).
    """

    received_at: datetime
    product_id: int
    name: str
    price: float
    discount: int
