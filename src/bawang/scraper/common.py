from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from bawang import config
from bawang.utils.net import fetch_text


def get_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def absolute_url(path: str) -> str:
    return urljoin(config.BASE_URL, path)


def fetch_soup(client, url: str) -> BeautifulSoup:
    html = fetch_text(client, url)
    return get_soup(html)


def normalize_url(url: Optional[str]) -> str:
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return absolute_url(url)
