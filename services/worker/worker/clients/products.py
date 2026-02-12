"""Client for fetching product search results from Wildberries mobile API."""

import logging

from worker.clients.base import BaseWBClient
from worker.exceptions import WBApiError

logger = logging.getLogger(__name__)

_SEARCH_ROUTE = "/__internal/search/exactmatch/ru/common/v14/search"


class ProductsClient(BaseWBClient):
    """Fetches product pages by search query from the WB mobile search API."""

    def _build_headers(self) -> dict[str, str]:
        """Extend base headers with search-specific fields."""
        headers = super()._build_headers()
        headers.update(
            {
                "Wb-AppReferer": "CatalogProductsVC",
                "X-ClientInfo": "appType=64;curr=rub;lang=ru;locale=ru",
                "Wb-AppVersion": "745",
            }
        )
        return headers

    def _build_query_params(self, search_query: str, page: int) -> dict[str, str]:
        """Build query parameters for the product search endpoint.

        Args:
            search_query: The searchQuery string obtained from category resolution.
            page: Page number (1-based).

        Returns:
            Dict of query parameters.
        """
        return {
            "ab_testing": "false",
            "appType": "64",
            "curr": "rub",
            "lang": "ru",
            "locale": "ru",
            "page": str(page),
            "query": search_query,
            "resultset": "catalog",
            "sort": "popular",
        }

    async def fetch_page(self, search_query: str, page: int) -> str:
        """Fetch a single page of product results as raw JSON.

        Args:
            search_query: The searchQuery string from category resolution.
            page: Page number (1-based).

        Returns:
            Raw JSON response string (for sending to Kafka as-is).

        Raises:
            WBApiError: If the API returns a non-200 response.
        """
        params = self._build_query_params(search_query, page)
        url = self._build_url(_SEARCH_ROUTE, params)
        headers = self._build_headers()

        logger.info("Fetching products page %d for query '%s'", page, search_query[:50])
        response = await self._session.get(url, headers=headers)

        if response.status_code != 200:
            raise WBApiError(
                response.status_code,
                f"Failed to fetch products page {page}: {response.text[:200]}",
            )

        logger.info("Products page %d fetched successfully (%d bytes)", page, len(response.text))
        return response.text
