from dataclasses import dataclass
from typing import List, Optional
import os
import sys

from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

try:
    from prompt_toolkit.application import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import HSplit
    from prompt_toolkit.styles import Style
    from prompt_toolkit.widgets import Frame, Label, RadioList
except ImportError:  # pragma: no cover - optional dependency
    Application = None
    KeyBindings = None
    Layout = None
    HSplit = None
    Style = None
    Frame = None
    Label = None
    RadioList = None


QUIT_WORDS = {"q", "quit", "exit"}
BACK_WORDS = {"b", "back", "0"}


@dataclass(frozen=True)
class Selection:
    action: str
    index: Optional[int] = None


def prompt_text(console, label: str, allow_quit: bool = True) -> Optional[str]:
    value = Prompt.ask(label, console=console).strip()
    if allow_quit and value.lower() in QUIT_WORDS:
        return None
    return value


def prompt_confirm(console, label: str, default: bool = True) -> bool:
    return Confirm.ask(label, console=console, default=default)


def use_arrow_ui() -> bool:
    value = os.getenv("BWN_ARROW_UI")
    if value:
        lowered = value.strip().lower()
        if lowered in {"0", "false", "no", "off"}:
            return False
        if lowered in {"1", "true", "yes", "on"}:
            return (
                (Application is not None or os.name == "nt")
                and sys.stdin.isatty()
                and sys.stdout.isatty()
            )
    return (
        (Application is not None or os.name == "nt")
        and sys.stdin.isatty()
        and sys.stdout.isatty()
    )


def _prompt_selection_text(
    console,
    label: str,
    count: int,
    allow_back: bool,
    allow_quit: bool,
) -> Selection:
    if count <= 0:
        raise ValueError("count must be positive")
    while True:
        value = Prompt.ask(label, console=console).strip()
        lowered = value.lower()
        if allow_quit and lowered in QUIT_WORDS:
            return Selection("quit")
        if allow_back and lowered in BACK_WORDS:
            return Selection("back")
        if value.isdigit():
            index = int(value)
            if 1 <= index <= count:
                return Selection("index", index - 1)
        hint = "number"
        if allow_back:
            hint += ", b=back"
        if allow_quit:
            hint += ", q=quit"
        console.print(f"Invalid input. Use {hint}.", style="red")


def _prompt_selection_arrow(
    label: str,
    items: List[str],
    allow_back: bool,
    allow_quit: bool,
) -> Selection:
    if not RadioList or not Application:
        raise RuntimeError("prompt_toolkit not available")

    values = [(idx, f"{idx + 1}. {item}") for idx, item in enumerate(items)]
    if allow_back:
        values.append((-1, "[Back]"))
    if allow_quit:
        values.append((-2, "[Quit]"))
    values.append((-3, "[Use Number Input]"))

    radio = RadioList(values=values)
    kb = KeyBindings()

    @kb.add("enter")
    def _accept(event) -> None:
        event.app.exit(result=radio.current_value)

    if allow_back:
        @kb.add("b")
        @kb.add("escape")
        def _back(event) -> None:
            event.app.exit(result=-1)

    if allow_quit:
        @kb.add("q")
        @kb.add("c-c")
        def _quit(event) -> None:
            event.app.exit(result=-2)

    @kb.add("n")
    def _numeric(event) -> None:
        event.app.exit(result=-3)

    hints = "Use Up/Down, Enter to select."
    if allow_back:
        hints += " b=back."
    if allow_quit:
        hints += " q=quit."
    hints += " n=number input."

    body = HSplit(
        [
            Label(text=label),
            Frame(radio, title="Select"),
            Label(text=hints),
        ]
    )
    style = Style.from_dict(
        {
            "dialog": "bg:#000000 #c0c0c0",
            "frame.border": "ansicyan",
            "label": "ansibrightcyan",
            "radiolist": "ansibrightwhite",
            "radiolist focused": "ansiblack bg:ansicyan",
        }
    )
    app = Application(
        layout=Layout(body),
        key_bindings=kb,
        full_screen=True,
        erase_when_done=True,
        mouse_support=False,
        style=style,
    )
    result = app.run()
    if result == -1:
        return Selection("back")
    if result == -2:
        return Selection("quit")
    if result == -3:
        return Selection("fallback")
    if result is None:
        return Selection("back" if allow_back else "quit")
    return Selection("index", int(result))


def _prompt_selection_native(
    console,
    label: str,
    items: List[str],
    allow_back: bool,
    allow_quit: bool,
) -> Selection:
    if os.name != "nt":
        raise RuntimeError("native arrow selection only supported on Windows")
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError("not a TTY")

    import msvcrt

    index = 0

    def read_key() -> str:
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            if ch2 == "H":
                return "UP"
            if ch2 == "P":
                return "DOWN"
            return ""
        if ch == "\r":
            return "ENTER"
        return ch

    def render_panel() -> Panel:
        current = items[index] if items else ""
        status = Text(
            f"Selected {index + 1}/{len(items)}: {current}", style="bold"
        )
        hint = "Up/Down to move, Enter to select."
        if allow_back:
            hint += " b=back."
        if allow_quit:
            hint += " q=quit."
        hint += " n=number input."
        return Panel(
            Group(status, Text(hint, style="dim")),
            title=label,
            title_align="left",
            border_style="cyan",
        )

    with Live(render_panel(), console=console, refresh_per_second=30, transient=True) as live:
        while True:
            key = read_key()
            if key == "UP":
                index = (index - 1) % len(items)
            elif key == "DOWN":
                index = (index + 1) % len(items)
            elif key == "ENTER":
                return Selection("index", index)
            elif key in {"b", "B"} and allow_back:
                return Selection("back")
            elif key in {"q", "Q"} and allow_quit:
                return Selection("quit")
            elif key in {"n", "N"}:
                return Selection("fallback")
            live.update(render_panel())


def prompt_selection(
    console,
    label: str,
    count: int,
    items: Optional[List[str]] = None,
    allow_back: bool = True,
    allow_quit: bool = True,
) -> Selection:
    if items and use_arrow_ui():
        selection = None
        try:
            if Application is not None:
                selection = _prompt_selection_arrow(
                    label, items, allow_back, allow_quit
                )
            if selection.action == "fallback":
                selection = None
            if selection:
                return selection
        except Exception:
            selection = None
        if selection is None:
            try:
                selection = _prompt_selection_native(
                    console, label, items, allow_back, allow_quit
                )
                if selection.action == "fallback":
                    selection = None
                if selection:
                    return selection
            except Exception:
                selection = None
        if selection is None:
            console.print(
                "Arrow mode unavailable. Using number input.",
                style="yellow",
            )
            return _prompt_selection_text(console, label, count, allow_back, allow_quit)
    return _prompt_selection_text(console, label, count, allow_back, allow_quit)
