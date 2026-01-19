import re
from typing import Iterable, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup


MEDIA_REGEX = re.compile(r"(https?://[^\\s'\"<>]+?\\.(?:m3u8|mp4)(?:\\?[^\\s'\"<>]+)?)")
PROTOCOL_RELATIVE = re.compile(r"(//[^\\s'\"<>]+?\\.(?:m3u8|mp4)(?:\\?[^\\s'\"<>]+)?)")


def _unique(values: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def extract_media_urls_from_html(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: List[str] = []

    for source in soup.select("source[src]"):
        candidates.append(source.get("src", ""))

    for video in soup.select("video[src]"):
        candidates.append(video.get("src", ""))

    for iframe in soup.select("iframe[src]"):
        candidates.append(iframe.get("src", ""))

    text = soup.get_text(" ", strip=True)
    candidates.extend(MEDIA_REGEX.findall(html))
    candidates.extend(PROTOCOL_RELATIVE.findall(html))
    candidates.extend(MEDIA_REGEX.findall(text))

    normalized: List[str] = []
    for url in candidates:
        if not url:
            continue
        if url.startswith("//"):
            url = "https:" + url
        if url.startswith("http://") or url.startswith("https://"):
            normalized.append(url)
        else:
            normalized.append(urljoin(base_url, url))

    return _unique([url for url in normalized if ".mp4" in url or ".m3u8" in url])
