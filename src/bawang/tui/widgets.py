from typing import List, Optional
from urllib.parse import urlparse

from rich import box
from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from bawang.models import Episode, QualityOption, SearchResult
from bawang.utils.text import truncate


APP_NAME = "Bawang-CLI"
APP_TAGLINE = "Search and stream anime (no downloads)"
APP_BANNER = r"""
    ____  ___ _       _____    _   ________
   / __ )/   | |     / /   |  / | / / ____/
  / __  / /| | | /| / / /| | /  |/ / / __  
 / /_/ / ___ | |/ |/ / ___ |/ /|  / /_/ /  
/_____/_/  |_|__/|__/_/  |_/_/ |_/\____/   
                                           
"""


def header_panel(section: str, subtitle: Optional[str] = None) -> Panel:
    banner = Text(APP_BANNER.strip("\n"), style="bold bright_cyan")
    tagline = Text(APP_TAGLINE, style="dim")
    lines = [Align.center(banner), Align.center(tagline)]
    if subtitle:
        lines.append(Align.center(Text(subtitle, style="dim")))
    return Panel(
        Group(*lines),
        title=section,
        title_align="left",
        border_style="cyan",
        box=box.SQUARE,
        padding=(1, 2),
    )


def message_panel(message: str, style: str = "yellow") -> Panel:
    return Panel(
        Text(message, style=style),
        border_style=style,
        box=box.SIMPLE,
        padding=(0, 1),
    )


def now_playing_panel(
    anime_title: str, episode_title: str, quality: Optional[str] = None
) -> Panel:
    label = f"{episode_title}"
    if quality:
        label = f"{label} ({quality})"
    return Panel(
        Group(
            Align.center(Text(anime_title, style="bold bright_cyan")),
            Align.center(Text(label, style="bold green")),
        ),
        title="Now Playing",
        title_align="left",
        border_style="green",
        box=box.SQUARE,
        padding=(1, 2),
    )


def _base_table(title: str) -> Table:
    table = Table(
        title=title,
        show_lines=False,
        box=box.SIMPLE,
        border_style="cyan",
        header_style="bold magenta",
        title_style="bold",
        caption="Type number, or b=back, q=quit",
        caption_style="dim",
        expand=True,
    )
    table.row_styles = ["", "dim"]
    return table


def search_results_table(results: List[SearchResult]) -> Table:
    table = _base_table("Search Results")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Title", style="bold")
    table.add_column("URL", style="dim")
    for idx, item in enumerate(results, start=1):
        table.add_row(str(idx), truncate(item.title, 60), truncate(item.url, 60))
    return table


def episodes_table(episodes: List[Episode]) -> Table:
    table = _base_table("Episodes")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Title", style="bold")
    table.add_column("URL", style="dim")
    for idx, item in enumerate(episodes, start=1):
        table.add_row(str(idx), truncate(item.title, 60), truncate(item.url, 60))
    return table


def quality_table(options: List[QualityOption]) -> Table:
    table = _base_table("Quality")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Label", style="bold")
    table.add_column("Host", style="magenta")
    table.add_column("URL", style="dim")
    for idx, item in enumerate(options, start=1):
        host = ""
        try:
            host = urlparse(item.url).netloc.replace("www.", "")
        except ValueError:
            host = ""
        table.add_row(str(idx), item.label, host, truncate(item.url, 60))
    return table
