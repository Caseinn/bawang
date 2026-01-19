import re
from typing import List, Tuple

from bawang.models import Episode
from bawang.scraper.common import fetch_soup, normalize_url
from bawang.utils.text import clean_whitespace


EPISODE_SELECTORS = [
    "div.episodelist a",
    "div.eplister a",
    "div.eps a",
    "div.epslst a",
]


def _format_episode_title(title: str) -> str:
    if not title:
        return title
    lowered = title.lower()
    if "episode" in lowered or lowered.startswith("ep"):
        return title
    match = re.search(r"(\d+(?:\.\d+)?)", title)
    if not match:
        return title
    return f"Episode {match.group(1)}"

def _episode_sort_key(episode: Episode) -> Tuple[int, float]:
    match = re.search(r"(\d+(?:\.\d+)?)", episode.title)
    if not match:
        return (0, 0.0)
    try:
        return (1, float(match.group(1)))
    except ValueError:
        return (0, 0.0)


def fetch_episodes(client, anime_url: str) -> List[Episode]:
    soup = fetch_soup(client, anime_url)
    episodes: List[Episode] = []
    seen = set()

    for selector in EPISODE_SELECTORS:
        for anchor in soup.select(selector):
            href = normalize_url(anchor.get("href"))
            if not href or href in seen:
                continue
            if "episode" not in href:
                continue
            title = clean_whitespace(anchor.get_text() or anchor.get("title") or "")
            title = _format_episode_title(title)
            if not title:
                continue
            episodes.append(Episode(title=title, url=href))
            seen.add(href)

    if not episodes:
        for anchor in soup.select("a"):
            href = normalize_url(anchor.get("href"))
            if not href or href in seen:
                continue
            if "episode" not in href:
                continue
            title = clean_whitespace(anchor.get_text() or anchor.get("title") or "")
            title = _format_episode_title(title)
            if not title:
                continue
            episodes.append(Episode(title=title, url=href))
            seen.add(href)

    with_numbers = [ep for ep in episodes if _episode_sort_key(ep)[0] == 1]
    if with_numbers:
        episodes = with_numbers
        episodes.sort(key=_episode_sort_key, reverse=True)

    return episodes
