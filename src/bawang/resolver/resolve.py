import base64
import json
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from bawang import config
from bawang.models import QualityOption
from bawang.resolver.heuristics import extract_media_urls_from_html
from bawang.resolver.hosts import resolve_embed_html
from bawang.utils.net import fetch_text, post_text
from bawang.utils.text import clean_whitespace


QUALITY_REGEX = re.compile(r"\\b(360|480|720|1080)p\\b", re.IGNORECASE)


def _quality_from_text(text: str) -> Optional[str]:
    match = QUALITY_REGEX.search(text)
    if not match:
        return None
    return f"{match.group(1)}p"


def _quality_rank(label: str, url: str) -> int:
    for source in (label, url):
        match = QUALITY_REGEX.search(source or "")
        if match:
            return int(match.group(1))
    return 0


def _host_score(url: str) -> int:
    netloc = urlparse(url).netloc.lower()
    for idx, host in enumerate(config.PREFERRED_HOSTS):
        if host in netloc:
            return len(config.PREFERRED_HOSTS) - idx
    return 0


def _maybe_decode_url(value: str) -> str:
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if not value or len(value) % 4 != 0:
        return value
    try:
        decoded = base64.b64decode(value).decode("utf-8", errors="ignore")
    except (ValueError, UnicodeDecodeError):
        return value
    if "http://" in decoded or "https://" in decoded:
        return decoded.strip()
    return value


def _add_option(options: List[QualityOption], seen: set, label: str, url: str) -> None:
    if not url or url in seen:
        return
    options.append(QualityOption(label=label, url=url))
    seen.add(url)


def _extract_player_options(soup) -> List[Dict[str, str]]:
    options: List[Dict[str, str]] = []
    for node in soup.select(".east_player_option"):
        post = node.get("data-post")
        nume = node.get("data-nume")
        kind = node.get("data-type")
        if not post or not nume or not kind:
            continue
        label = clean_whitespace(node.get_text() or "")
        if not label:
            label = f"Option {nume}"
        options.append({"post": str(post), "nume": str(nume), "type": str(kind), "label": label})
    return options


def _extract_blogger_streams(html: str) -> List[str]:
    urls: List[str] = []
    marker = "VIDEO_CONFIG"
    idx = html.find(marker)
    if idx != -1:
        start = html.find("{", idx)
        end = html.find("</script>", start)
        if start != -1 and end != -1:
            payload = html[start:end]
            end_brace = payload.rfind("}")
            if end_brace != -1:
                payload = payload[: end_brace + 1]
                try:
                    data = json.loads(payload)
                    for stream in data.get("streams", []) or []:
                        play_url = stream.get("play_url")
                        if play_url:
                            urls.append(play_url)
                except json.JSONDecodeError:
                    urls = []
    if not urls:
        for play_url in re.findall(r'\"play_url\"\\s*:\\s*\"(https?://[^\\\"]+)\"', html):
            urls.append(play_url)
    return urls


def _resolve_iframe_src(client, iframe_url: str, referer: str) -> List[str]:
    if ".mp4" in iframe_url or ".m3u8" in iframe_url:
        return [iframe_url]
    if "blogger.com/video.g" in iframe_url:
        try:
            html = fetch_text(client, iframe_url, referer=referer)
        except Exception:
            return []
        return _extract_blogger_streams(html)
    try:
        html = fetch_text(client, iframe_url, referer=referer)
    except Exception:
        return []
    return extract_media_urls_from_html(html, iframe_url)


def _add_from_html(
    client,
    html: str,
    base_url: str,
    label: str,
    options: List[QualityOption],
    seen: set,
    referer: str,
) -> None:
    for media_url in extract_media_urls_from_html(html, base_url):
        _add_option(options, seen, label, media_url)
    soup = BeautifulSoup(html, "html.parser")
    for iframe in soup.select("iframe[src]"):
        src = iframe.get("src") or ""
        if not src:
            continue
        src = urljoin(base_url, src)
        for media_url in _resolve_iframe_src(client, src, referer=referer):
            _add_option(options, seen, label, media_url)


def resolve_video_links(client, episode_url: str) -> List[QualityOption]:
    html = fetch_text(client, episode_url)
    soup = BeautifulSoup(html, "html.parser")
    options: List[QualityOption] = []
    seen = set()

    for media_url in extract_media_urls_from_html(html, episode_url):
        _add_option(options, seen, "auto", media_url)

    for anchor in soup.select("a"):
        text = clean_whitespace(anchor.get_text() or "")
        href = anchor.get("href") or ""
        if not href:
            continue
        href = urljoin(episode_url, href)
        quality = _quality_from_text(text) or _quality_from_text(href) or "auto"
        if ".mp4" in href or ".m3u8" in href:
            _add_option(options, seen, quality, href)

    embed_candidates: List[str] = []
    for tag in soup.select("[data-video], [data-embed], [data-src], [data-url], iframe[src]"):
        candidate = (
            tag.get("data-video")
            or tag.get("data-embed")
            or tag.get("data-src")
            or tag.get("data-url")
            or tag.get("src")
            or ""
        )
        if not candidate:
            continue
        candidate = _maybe_decode_url(candidate)
        candidate = urljoin(episode_url, candidate)
        embed_candidates.append(candidate)

    for anchor in soup.select("div.download a[href]"):
        href = anchor.get("href") or ""
        if not href:
            continue
        href = urljoin(episode_url, href)
        if href.startswith("http://") or href.startswith("https://"):
            embed_candidates.append(href)

    for candidate in embed_candidates[:10]:
        if candidate in seen:
            continue
        try:
            embed_html = fetch_text(client, candidate, referer=episode_url)
        except Exception:
            continue
        for media_url in resolve_embed_html(embed_html, candidate):
            _add_option(options, seen, "auto", media_url)

    player_options = _extract_player_options(soup)
    if player_options:
        ajax_url = urljoin(episode_url, config.ADMIN_AJAX_PATH)
        for option in player_options:
            payload = {
                "action": "player_ajax",
                "post": option["post"],
                "nume": option["nume"],
                "type": option["type"],
            }
            try:
                response_html = post_text(client, ajax_url, data=payload, referer=episode_url)
            except Exception:
                continue
            label = option["label"]
            _add_from_html(
                client,
                response_html,
                episode_url,
                label or "auto",
                options,
                seen,
                referer=episode_url,
            )

    options.sort(
        key=lambda item: (_host_score(item.url), _quality_rank(item.label, item.url)),
        reverse=True,
    )
    return options
