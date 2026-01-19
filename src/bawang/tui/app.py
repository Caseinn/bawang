from rich.console import Console

import httpx

try:
    import requests
except ImportError:  # pragma: no cover - optional fallback
    requests = None

from bawang.player import ffplay, mpv
from bawang.player.detect import detect_player
from bawang.resolver.resolve import resolve_video_links
from bawang.scraper.episodes import fetch_episodes
from bawang.scraper.search import search_anime
from bawang.tui.events import prompt_confirm
from bawang.tui.screens import (
    show_episode_list,
    show_home,
    show_quality_select,
    show_search_results,
)
from bawang.tui.widgets import now_playing_panel
from bawang.utils.log import configure_logging
from bawang.utils.net import get_client


def _format_error(exc: Exception) -> str:
    status = None
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
    elif requests and isinstance(exc, requests.HTTPError) and exc.response is not None:
        status = exc.response.status_code
    if status in {403, 429}:
        return (
            "Blocked by the site (HTTP 403/429). Try again later or switch domain."
        )
    return f"{exc.__class__.__name__}: {exc}"


def _format_episode_title(raw_title: str) -> str:
    lowered = raw_title.lower()
    if "episode" in lowered or lowered.startswith("ep"):
        return raw_title
    return f"Episode {raw_title}"


def run_app() -> None:
    configure_logging()
    console = Console()
    player = detect_player()
    if not player:
        console.print("No media player found. Install mpv or ffplay.", style="red")
        return

    with get_client() as client:
        while True:
            query = show_home(console)
            if query is None:
                return
            if not query:
                console.print("Empty query. Type a title or q to quit.", style="yellow")
                continue

            try:
                with console.status("Searching..."):
                    results = search_anime(client, query)
            except Exception as exc:  # noqa: BLE001 - user facing error
                console.print(_format_error(exc), style="red")
                if prompt_confirm(console, "Search again?", default=True):
                    continue
                return

            if not results:
                console.print("No results found.", style="yellow")
                if prompt_confirm(console, "Search again?", default=True):
                    continue
                return

            search_again = False
            while True:
                selection, chosen = show_search_results(console, query, results)
                if selection.action == "quit":
                    return
                if selection.action == "back":
                    break
                if not chosen:
                    continue

                try:
                    with console.status("Fetching episodes..."):
                        episodes = fetch_episodes(client, chosen.url)
                except Exception as exc:  # noqa: BLE001 - user facing error
                    console.print(_format_error(exc), style="red")
                    if prompt_confirm(console, "Back to results?", default=True):
                        continue
                    return

                if not episodes:
                    console.print("No episodes found.", style="yellow")
                    if prompt_confirm(console, "Back to results?", default=True):
                        continue
                    return

                while True:
                    selection, episode = show_episode_list(
                        console, chosen.title, episodes
                    )
                    if selection.action == "quit":
                        return
                    if selection.action == "back":
                        break
                    if not episode:
                        continue

                    try:
                        with console.status("Resolving video links..."):
                            options = resolve_video_links(client, episode.url)
                    except Exception as exc:  # noqa: BLE001 - user facing error
                        console.print(_format_error(exc), style="red")
                        if prompt_confirm(console, "Back to episodes?", default=True):
                            continue
                        return

                    if not options:
                        console.print("No playable links found.", style="red")
                        if prompt_confirm(console, "Back to episodes?", default=True):
                            continue
                        return

                    selection, choice = show_quality_select(
                        console, episode.title, options
                    )
                    if selection.action == "quit":
                        return
                    if selection.action == "back":
                        continue
                    if not choice:
                        continue

                    title = episode.title
                    console.clear()
                    console.print(
                        now_playing_panel(
                            chosen.title,
                            _format_episode_title(title),
                            quality=choice.label,
                        )
                    )
                    if player == "mpv":
                        mpv.play(choice.url, title)
                    else:
                        ffplay.play(choice.url, title)

                    if prompt_confirm(
                        console,
                        "Play another episode from this anime?",
                        default=True,
                    ):
                        continue
                    if prompt_confirm(console, "Search another anime?", default=True):
                        search_again = True
                        break
                    return
                if search_again:
                    break
            if search_again:
                continue
