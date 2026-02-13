"""Pydantic models for parsed Wildberries product data."""

from datetime import datetime  # noqa: TC003 - Pydantic needs this at runtime

from pydantic import BaseModel, computed_field


class ParsedProduct(BaseModel):
    """A single parsed product ready for producing to the wb-products topic.

    Attributes:
        received_at: Timestamp when the raw data was received and parsed.
        product_id: Wildberries product identifier.
        name: Product display name.
        price: Product price in rubles (converted from kopecks).
        base_price: Original price in rubles before any discounts (converted from kopecks).
        discount: Discount percentage (0-100).
        url: Direct link to the product page on Wildberries.
    """

    received_at: datetime
    product_id: int
    name: str
    price: float
    base_price: float
    discount: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        """Direct link to the product page on Wildberries."""
        return f"https://www.wildberries.ru/catalog/{self.product_id}/detail.aspx"
