"""Base HTTP client for Wildberries mobile API with undetectable TLS fingerprint."""

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlencode

if TYPE_CHECKING:
    from curl_cffi.requests import AsyncSession

logger = logging.getLogger(__name__)


class BaseWBClient:
    """Base client providing shared headers, URL building, and iOS impersonation.

    All WB API clients inherit from this to get consistent request configuration.
    Uses curl_cffi with Safari impersonation for undetectable TLS fingerprint.
    """

    def __init__(self, session: AsyncSession, base_url: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")

    def _build_headers(self) -> dict[str, str]:
        """Generate iOS mobile app headers matching Wildberries app traffic."""
        return {
            "Host": "api-ios.wildberries.ru",
            "User-Agent": (
                "Wildberries/7.4.5001 (RU.WILDBERRIES.MOBILEAPP; build:14026313; iOS 17.6.1) Alamofire/5.9.1"
            ),
            "devicename": "iOS, iPhone15,2",
            "WB-AppLanguage": "ru",
            "deviceToken": "",
            "Site-Locale": "ru",
            "Connection": "keep-alive",
            "Accept-Language": "ru-KZ;q=1.0, en-KZ;q=0.9, el-GR;q=0.8, lt-LT;q=0.7",
            "Wb-AppType": "ios",
            "Accept": "*/*",
            "wb-appversion": "745001",
            "X-ClientInfo": (
                "appType=64;curr=rub;spp=40;dest=-1257786;lang=ru;locale=ru;hide_dtype=11;hide_vflags=4563402752"
            ),
        }

    def _build_url(self, route: str, params: dict[str, str] | None = None) -> str:
        """Build a full URL from route and optional query parameters.

        Args:
            route: API route path (e.g. '/__internal/catalog/menu/v12/api').
            params: Optional query parameters dict.

        Returns:
            Fully qualified URL string.
        """
        url = f"{self._base_url}{route}"
        if params:
            url = f"{url}?{urlencode(params)}"
        return url
