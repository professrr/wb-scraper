"""Client for fetching and resolving Wildberries category tree."""

import logging
from typing import Any, cast
from urllib.parse import urlparse

from worker.clients.base import BaseWBClient
from worker.exceptions import CategoryNotFoundError, WBApiError

logger = logging.getLogger(__name__)

_CATALOG_ROUTE = "/__internal/catalog/menu/v12/api"


class CategoriesClient(BaseWBClient):
    """Fetches the WB category tree and resolves a URL path to a searchQuery string."""

    def _build_headers(self) -> dict[str, str]:
        """Extend base headers with catalog-specific fields."""
        headers = super()._build_headers()
        return headers

    def _build_query_params(self) -> dict[str, str]:
        """Build query parameters for the catalog menu endpoint."""
        return {
            "ab_testing": "false",
            "lang": "ru",
        }

    async def fetch_categories(self) -> dict[str, Any]:
        """Fetch the full category tree from WB mobile API.

        Returns:
            Raw parsed JSON dict of the category tree.

        Raises:
            WBApiError: If the API returns a non-200 response.
        """
        url = self._build_url(_CATALOG_ROUTE, self._build_query_params())
        headers = self._build_headers()

        logger.info("Fetching category tree from %s", _CATALOG_ROUTE)
        response = await self._session.get(url, headers=headers)

        if response.status_code != 200:
            raise WBApiError(response.status_code, f"Failed to fetch categories: {response.text[:200]}")

        data = cast("dict[str, Any]", response.json())  # pyright: ignore[reportUnknownMemberType]
        logger.info("Category tree fetched successfully")
        return data

    def resolve_category(self, category_url: str, tree: dict[str, Any]) -> str:
        """Resolve a WB category URL to a searchQuery string.

        Parses the URL path and searches the category tree (root key ``data``,
        children key ``nodes``) for a node whose ``url`` field matches the
        full catalog path.

        Args:
            category_url: Full WB category URL
                (e.g. 'https://www.wildberries.ru/catalog/elektronika/.../igrovye-konsoli').
            tree: Raw category tree dict from fetch_categories().

        Returns:
            The searchQuery string for the matched category.

        Raises:
            CategoryNotFoundError: If no matching category is found in the tree.
        """
        url_path = urlparse(category_url).path.rstrip("/")
        logger.info("Resolving category for URL path '%s'", url_path)

        if not url_path or url_path == "/catalog":
            raise CategoryNotFoundError(url_path)

        root_nodes: list[dict[str, Any]] = tree.get("data", [])
        logger.debug("Category tree has %d root nodes", len(root_nodes))

        node = self._find_node_by_url(root_nodes, url_path)
        if node is None:
            logger.warning("No node matched URL path '%s'", url_path)
            raise CategoryNotFoundError(url_path)

        search_query: str | None = node.get("searchQuery") or node.get("query")
        if not search_query:
            logger.warning("Node matched but has no searchQuery/query: %s", node.get("name"))
            raise CategoryNotFoundError(url_path)

        logger.info(
            "Category resolved: path='%s' -> name='%s', searchQuery='%s'",
            url_path,
            node.get("name"),
            search_query,
        )
        return search_query

    def _find_node_by_url(self, nodes: list[dict[str, Any]], target_url: str) -> dict[str, Any] | None:
        """Recursively search a list of category nodes for a matching URL path.

        The WB category tree uses ``data`` at the root level and ``nodes``
        for nested children.  Each node stores its full URL path in the
        ``url`` field (e.g. ``/catalog/elektronika/.../igrovye-konsoli``).

        Args:
            nodes: List of category node dicts to search.
            target_url: Full URL path to match (e.g. '/catalog/.../igrovye-konsoli').

        Returns:
            The matching node dict, or None if not found.
        """
        for node in nodes:
            node_url: str | None = node.get("url")
            if node_url == target_url:
                logger.debug("Matched node: id=%s, name='%s'", node.get("id"), node.get("name"))
                return node

            children: list[dict[str, Any]] = node.get("nodes", [])
            if children:
                result = self._find_node_by_url(children, target_url)
                if result is not None:
                    return result

        return None
