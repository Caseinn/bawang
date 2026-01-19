from typing import List, Optional
from urllib.parse import urlparse

from rich.console import Console
from rich.text import Text

from bawang.models import Episode, QualityOption, SearchResult
from bawang.tui.events import Selection, prompt_selection, prompt_text, use_arrow_ui
from bawang.tui.widgets import (
    episodes_table,
    header_panel,
    message_panel,
    quality_table,
    search_results_table,
)
from bawang.utils.text import truncate


def _host_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except ValueError:
        return ""


def _build_labels(values: List[str], max_len: int = 80) -> List[str]:
    return [truncate(value, max_len) for value in values]


def show_home(console: Console) -> Optional[str]:
    console.clear()
    console.print(header_panel("Search"))
    console.print(Text("Enter an anime title to search.", style="dim"))
    console.print(Text("Tip: type q to quit.", style="dim"))
    return prompt_text(console, "Search anime")


def show_search_results(
    console: Console, query: str, results: List[SearchResult]
) -> tuple[Selection, Optional[SearchResult]]:
    console.clear()
    console.print(
        header_panel("Results", subtitle=f"Query: {query} - {len(results)} results")
    )
    if not results:
        console.print(message_panel("No results found.", style="yellow"))
        return Selection("back"), None
    console.print(search_results_table(results))
    if use_arrow_ui():
        console.print(
            Text(
                "Arrow mode enabled. Use Up/Down, Enter, or press n for numbers.",
                style="dim",
            )
        )
    labels = _build_labels(
        [f"{item.title} - {truncate(item.url, 40)}" for item in results]
    )
    selection = prompt_selection(
        console,
        "Select result",
        len(results),
        items=labels,
        allow_back=True,
        allow_quit=True,
    )
    if selection.action != "index":
        return selection, None
    return selection, results[selection.index or 0]


def show_episode_list(
    console: Console, anime_title: str, episodes: List[Episode]
) -> tuple[Selection, Optional[Episode]]:
    console.clear()
    console.print(
        header_panel("Episodes", subtitle=f"{anime_title} - {len(episodes)} episodes")
    )
    if not episodes:
        console.print(message_panel("No episodes found.", style="yellow"))
        return Selection("back"), None
    console.print(episodes_table(episodes))
    if use_arrow_ui():
        console.print(
            Text(
                "Arrow mode enabled. Use Up/Down, Enter, or press n for numbers.",
                style="dim",
            )
        )
    labels = _build_labels(
        [f"{item.title} - {truncate(item.url, 40)}" for item in episodes]
    )
    selection = prompt_selection(
        console,
        "Select episode",
        len(episodes),
        items=labels,
        allow_back=True,
        allow_quit=True,
    )
    if selection.action != "index":
        return selection, None
    return selection, episodes[selection.index or 0]


def show_quality_select(
    console: Console, episode_title: str, options: List[QualityOption]
) -> tuple[Selection, Optional[QualityOption]]:
    console.clear()
    console.print(
        header_panel("Quality", subtitle=f"{episode_title} - {len(options)} options")
    )
    if not options:
        console.print(
            message_panel(
                "No playable links found. Try another episode or change domain.",
                style="red",
            )
        )
        return Selection("back"), None
    console.print(quality_table(options))
    if use_arrow_ui():
        console.print(
            Text(
                "Arrow mode enabled. Use Up/Down, Enter, or press n for numbers.",
                style="dim",
            )
        )
    option_labels: List[str] = []
    for item in options:
        host = _host_from_url(item.url)
        label = item.label
        if host:
            label = f"{label} - {host}"
        option_labels.append(label)
    labels = _build_labels(option_labels)
    selection = prompt_selection(
        console,
        "Select quality",
        len(options),
        items=labels,
        allow_back=True,
        allow_quit=True,
    )
    if selection.action != "index":
        return selection, None
    return selection, options[selection.index or 0]
