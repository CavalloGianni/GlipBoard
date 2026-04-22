from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import AyatanaAppIndicator3 as AppIndicator3
from gi.repository import GLib, Gtk


APP_ID = "glipboard-tray"
APP_TITLE = "GlipBoard"
MAX_MENU_HISTORY_ITEMS = 5
PROJECT_DIR = Path(__file__).resolve().parent
APP_ICON_PATH = (
    PROJECT_DIR / "logo.2816x1536.png"
    if (PROJECT_DIR / "logo.2816x1536.png").exists()
    else PROJECT_DIR / "logo.png"
)


def get_data_dir() -> Path:
    override = os.environ.get("GLIPBOARD_DATA_DIR") or os.environ.get("MYCLIPBOARD_DATA_DIR")
    if override:
        data_dir = Path(override).expanduser()
    else:
        data_dir = PROJECT_DIR / ".glipboard-data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


class CommandChannel:
    def __init__(self, base_dir: Path) -> None:
        self.path = base_dir / "commands.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def write_command(self, command: str, payload: dict | None = None) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"command": command, "payload": payload or {}, "ts": time.time()}) + "\n")


class HistoryStore:
    def __init__(self, base_dir: Path) -> None:
        self.path = base_dir / "clipboard-history.json"

    def load(self) -> list[str]:
        if not self.path.exists():
            return []

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

        items = payload.get("items", [])
        if not isinstance(items, list):
            return []

        return [item for item in items if isinstance(item, str)][:MAX_MENU_HISTORY_ITEMS]


def summarize_text(text: str, max_length: int = 42) -> str:
    single_line = " ".join(text.split())
    if not single_line:
        return "(Testo vuoto)"
    if len(single_line) <= max_length:
        return single_line
    return f"{single_line[: max_length - 3]}..."


def rebuild_menu(menu: Gtk.Menu, channel: CommandChannel, history_store: HistoryStore) -> None:
    for child in menu.get_children():
        menu.remove(child)

    open_item = Gtk.MenuItem(label="Apri")
    open_item.connect("activate", lambda *_args: channel.write_command("show"))
    menu.append(open_item)

    hide_item = Gtk.MenuItem(label="Nascondi")
    hide_item.connect("activate", lambda *_args: channel.write_command("hide"))
    menu.append(hide_item)

    menu.append(Gtk.SeparatorMenuItem())

    history_items = history_store.load()
    if history_items:
        history_header = Gtk.MenuItem(label="Cronologia")
        history_header.set_sensitive(False)
        menu.append(history_header)

        for text in history_items:
            item = Gtk.MenuItem(label=summarize_text(text))
            item.connect("activate", lambda *_args, text=text: channel.write_command("copy", {"text": text}))
            menu.append(item)
    else:
        empty_item = Gtk.MenuItem(label="(Nessun testo salvato)")
        empty_item.set_sensitive(False)
        menu.append(empty_item)

    menu.append(Gtk.SeparatorMenuItem())

    clear_item = Gtk.MenuItem(label="Pulisci cronologia")
    clear_item.connect("activate", lambda *_args: channel.write_command("clear"))
    menu.append(clear_item)

    menu.append(Gtk.SeparatorMenuItem())

    quit_item = Gtk.MenuItem(label="Esci")
    quit_item.connect("activate", lambda *_args: channel.write_command("quit"))
    menu.append(quit_item)

    menu.show_all()


def refresh_menu(menu: Gtk.Menu, channel: CommandChannel, history_store: HistoryStore) -> bool:
    rebuild_menu(menu, channel, history_store)
    return True


def main() -> int:
    data_dir = get_data_dir()
    channel = CommandChannel(data_dir)
    history_store = HistoryStore(data_dir)

    indicator = AppIndicator3.Indicator.new(
        APP_ID,
        str(APP_ICON_PATH) if APP_ICON_PATH.exists() else "edit-paste-symbolic",
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
    )
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    indicator.set_title(APP_TITLE)
    if APP_ICON_PATH.exists():
        indicator.set_icon_full(str(APP_ICON_PATH), APP_TITLE)

    menu = Gtk.Menu()
    rebuild_menu(menu, channel, history_store)
    indicator.set_menu(menu)

    GLib.timeout_add_seconds(2, refresh_menu, menu, channel, history_store)

    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
