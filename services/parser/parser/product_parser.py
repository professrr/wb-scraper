"""Parse raw WB API JSON into structured product models."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from parser.models import ParsedProduct

logger = logging.getLogger(__name__)


def parse_products(raw_json: str) -> list[ParsedProduct]:
    """Parse raw WB API JSON response into a list of ParsedProduct.

    Extracts the products array from the response, calculates price in rubles
    and discount percentage for each product. Products with missing sizes or
    price data are skipped with a warning log.

    Args:
        raw_json: Raw JSON string from the wb-category Kafka topic.

    Returns:
        List of validated ParsedProduct instances.

    Raises:
        json.JSONDecodeError: If raw_json is not valid JSON (caller handles).
    """
    data: dict[str, Any] = json.loads(raw_json)
    raw_products: list[dict[str, Any]] = data.get("products", [])

    if not raw_products:
        logger.warning("No products found in message")
        return []

    received_at = datetime.now(UTC)
    products: list[ParsedProduct] = []

    for item in raw_products:
        product_id: int | None = item.get("id")
        name: str | None = item.get("name")

        if product_id is None or name is None:
            logger.warning("Skipping product with missing id or name: %s", item.get("id"))
            continue

        sizes: list[dict[str, Any]] = item.get("sizes", [])
        if not sizes:
            logger.warning("Skipping product %d (%s): no sizes data", product_id, name)
            continue

        price_data: dict[str, int] | None = sizes[0].get("price")
        if not price_data:
            logger.warning("Skipping product %d (%s): no price data", product_id, name)
            continue

        basic: int = price_data.get("basic", 0)
        product_price: int = price_data.get("product", 0)

        price_rubles = product_price / 100
        discount = round((basic - product_price) / basic * 100) if basic > 0 else 0

        products.append(
            ParsedProduct(
                received_at=received_at,
                product_id=product_id,
                name=name,
                price=price_rubles,
                discount=discount,
            )
        )

    logger.info("Parsed %d products from message", len(products))
    return products
