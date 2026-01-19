import logging
from typing import Dict, Optional
from urllib.parse import urlparse

import httpx

from bawang import config

try:
    import requests
except ImportError:  # pragma: no cover - optional fallback
    requests = None

try:
    import cloudscraper
except ImportError:  # pragma: no cover - optional fallback
    cloudscraper = None


LOGGER = logging.getLogger(__name__)
FALLBACK_STATUSES = {403, 429}


def build_headers(
    extra: Optional[Dict[str, str]] = None, referer: Optional[str] = None
) -> Dict[str, str]:
    headers = {
        "User-Agent": config.USER_AGENT,
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Ch-Ua": '"Chromium";v="120", "Google Chrome";v="120", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
    }
    if referer:
        headers["Referer"] = referer
        headers["Origin"] = referer
    if extra:
        headers.update(extra)
    return headers


def _referer_for(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return config.BASE_URL
    return f"{parsed.scheme}://{parsed.netloc}"


class HttpClient:
    def __init__(self) -> None:
        self._httpx = httpx.Client(
            headers=build_headers(),
            timeout=config.DEFAULT_TIMEOUT,
            follow_redirects=True,
        )
        self._requests = requests.Session() if requests else None
        if self._requests:
            self._requests.headers.update(build_headers())
        self._cloudscraper = cloudscraper.create_scraper() if cloudscraper else None
        if self._cloudscraper:
            self._cloudscraper.headers.update(build_headers())

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self._httpx.close()
        if self._requests:
            self._requests.close()
        if self._cloudscraper:
            self._cloudscraper.close()

    def get_text(self, url: str, referer: Optional[str] = None) -> str:
        last_error: Exception | None = None
        for name, getter in self._providers():
            if getter is None:
                continue
            try:
                return getter(url, referer)
            except Exception as exc:  # noqa: BLE001 - surface final error
                last_error = exc
                if not _is_retryable(exc):
                    raise
                LOGGER.debug("Request blocked (%s), trying fallback...", name)
        if last_error:
            raise last_error
        raise RuntimeError("No HTTP client available")

    def _providers(self):
        return [
            ("httpx", self._get_with_httpx),
            ("cloudscraper", self._get_with_cloudscraper if self._cloudscraper else None),
            ("requests", self._get_with_requests if self._requests else None),
        ]

    def post_text(
        self, url: str, data: Dict[str, str], referer: Optional[str] = None
    ) -> str:
        last_error: Exception | None = None
        for name, poster in self._post_providers():
            if poster is None:
                continue
            try:
                return poster(url, data, referer)
            except Exception as exc:  # noqa: BLE001 - surface final error
                last_error = exc
                if not _is_retryable(exc):
                    raise
                LOGGER.debug("Post blocked (%s), trying fallback...", name)
        if last_error:
            raise last_error
        raise RuntimeError("No HTTP client available")

    def _post_providers(self):
        return [
            ("httpx", self._post_with_httpx),
            ("cloudscraper", self._post_with_cloudscraper if self._cloudscraper else None),
            ("requests", self._post_with_requests if self._requests else None),
        ]

    def _get_with_httpx(self, url: str, referer: Optional[str] = None) -> str:
        headers = build_headers(referer=referer or _referer_for(url))
        response = self._httpx.get(url, headers=headers)
        if response.status_code in FALLBACK_STATUSES:
            self._warm_httpx()
            response = self._httpx.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def _post_with_httpx(
        self, url: str, data: Dict[str, str], referer: Optional[str] = None
    ) -> str:
        headers = build_headers(referer=referer or _referer_for(url))
        response = self._httpx.post(url, data=data, headers=headers)
        if response.status_code in FALLBACK_STATUSES:
            self._warm_httpx()
            response = self._httpx.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.text

    def _get_with_requests(self, url: str, referer: Optional[str] = None) -> str:
        if not self._requests:
            raise RuntimeError("requests not available")
        headers = build_headers(referer=referer or _referer_for(url))
        response = self._requests.get(
            url, headers=headers, timeout=config.DEFAULT_TIMEOUT, allow_redirects=True
        )
        if response.status_code in FALLBACK_STATUSES:
            self._warm_requests()
            response = self._requests.get(
                url, headers=headers, timeout=config.DEFAULT_TIMEOUT, allow_redirects=True
            )
        response.raise_for_status()
        return response.text

    def _post_with_requests(
        self, url: str, data: Dict[str, str], referer: Optional[str] = None
    ) -> str:
        if not self._requests:
            raise RuntimeError("requests not available")
        headers = build_headers(referer=referer or _referer_for(url))
        response = self._requests.post(
            url, data=data, headers=headers, timeout=config.DEFAULT_TIMEOUT
        )
        if response.status_code in FALLBACK_STATUSES:
            self._warm_requests()
            response = self._requests.post(
                url, data=data, headers=headers, timeout=config.DEFAULT_TIMEOUT
            )
        response.raise_for_status()
        return response.text

    def _get_with_cloudscraper(self, url: str, referer: Optional[str] = None) -> str:
        if not self._cloudscraper:
            raise RuntimeError("cloudscraper not available")
        headers = build_headers(referer=referer or _referer_for(url))
        response = self._cloudscraper.get(
            url, headers=headers, timeout=config.DEFAULT_TIMEOUT
        )
        if response.status_code in FALLBACK_STATUSES:
            self._warm_cloudscraper()
            response = self._cloudscraper.get(
                url, headers=headers, timeout=config.DEFAULT_TIMEOUT
            )
        response.raise_for_status()
        return response.text

    def _post_with_cloudscraper(
        self, url: str, data: Dict[str, str], referer: Optional[str] = None
    ) -> str:
        if not self._cloudscraper:
            raise RuntimeError("cloudscraper not available")
        headers = build_headers(referer=referer or _referer_for(url))
        response = self._cloudscraper.post(
            url, data=data, headers=headers, timeout=config.DEFAULT_TIMEOUT
        )
        if response.status_code in FALLBACK_STATUSES:
            self._warm_cloudscraper()
            response = self._cloudscraper.post(
                url, data=data, headers=headers, timeout=config.DEFAULT_TIMEOUT
            )
        response.raise_for_status()
        return response.text

    def _warm_httpx(self) -> None:
        try:
            self._httpx.get(config.BASE_URL, headers=build_headers())
        except Exception:
            return

    def _warm_requests(self) -> None:
        if not self._requests:
            return
        try:
            self._requests.get(
                config.BASE_URL,
                headers=build_headers(),
                timeout=config.DEFAULT_TIMEOUT,
            )
        except Exception:
            return

    def _warm_cloudscraper(self) -> None:
        if not self._cloudscraper:
            return
        try:
            self._cloudscraper.get(
                config.BASE_URL,
                headers=build_headers(),
                timeout=config.DEFAULT_TIMEOUT,
            )
        except Exception:
            return


def _is_retryable(exc: Exception) -> bool:
    status = _status_from_exception(exc)
    if status is not None:
        return status in FALLBACK_STATUSES
    if isinstance(exc, httpx.RequestError):
        return True
    if requests and isinstance(exc, requests.RequestException):
        return True
    return False


def _status_from_exception(exc: Exception) -> Optional[int]:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code
    if requests and isinstance(exc, requests.HTTPError):
        if exc.response is None:
            return None
        return exc.response.status_code
    return None


def get_client() -> HttpClient:
    return HttpClient()


def fetch_text(client, url: str, referer: Optional[str] = None) -> str:
    if hasattr(client, "get_text"):
        return client.get_text(url, referer=referer)
    headers = build_headers(referer=referer or _referer_for(url))
    response = client.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def post_text(
    client, url: str, data: Dict[str, str], referer: Optional[str] = None
) -> str:
    if hasattr(client, "post_text"):
        return client.post_text(url, data, referer=referer)
    headers = build_headers(referer=referer or _referer_for(url))
    response = client.post(url, data=data, headers=headers)
    response.raise_for_status()
    return response.text
