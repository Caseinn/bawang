from typing import List
from urllib.parse import quote_plus

from bawang import config
from bawang.models import SearchResult
from bawang.scraper.common import fetch_soup, normalize_url
from bawang.utils.text import clean_whitespace


CARD_SELECTORS = [
    "div.animepost",
    "div.animpos",
    "div.post-show",
    "div.bs",
    "div.bsx",
]


def _extract_from_card(card) -> SearchResult | None:
    anchor = card.select_one("a")
    if not anchor:
        return None
    href = normalize_url(anchor.get("href"))
    if not href:
        return None
    title = anchor.get("title") or anchor.get_text() or ""
    heading = card.select_one("h2, h3")
    if heading and heading.get_text(strip=True):
        title = heading.get_text()
    title = clean_whitespace(title)
    if not title:
        return None
    img = card.select_one("img")
    thumb = ""
    if img:
        thumb = img.get("data-src") or img.get("src") or ""
        thumb = normalize_url(thumb)
    return SearchResult(title=title, url=href, thumbnail=thumb or None)


def search_anime(client, query: str) -> List[SearchResult]:
    safe_query = quote_plus(query.strip())
    url = config.BASE_URL + config.SEARCH_PATH.format(query=safe_query)
    soup = fetch_soup(client, url)
    results: List[SearchResult] = []
    seen = set()

    for selector in CARD_SELECTORS:
        for card in soup.select(selector):
            result = _extract_from_card(card)
            if not result or result.url in seen:
                continue
            results.append(result)
            seen.add(result.url)

    if results:
        return results

    for anchor in soup.select("h2 a, h3 a, a[rel='bookmark']"):
        href = normalize_url(anchor.get("href"))
        title = clean_whitespace(anchor.get_text() or anchor.get("title") or "")
        if not href or not title or href in seen:
            continue
        results.append(SearchResult(title=title, url=href))
        seen.add(href)

    return results
