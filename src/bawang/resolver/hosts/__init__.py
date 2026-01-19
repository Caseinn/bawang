from typing import List

from bawang.resolver.heuristics import extract_media_urls_from_html


def resolve_embed_html(html: str, base_url: str) -> List[str]:
    return extract_media_urls_from_html(html, base_url)
