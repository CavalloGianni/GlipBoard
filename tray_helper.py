from __future__ import annotations

import json
import os
import shutil
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
APP_ICON_PATH = PROJECT_DIR / "image (2).png"
APP_DATA_DIRNAME = "glipboard"
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
LEGACY_DATA_FILENAMES = ("clipboard-history.json", "settings.json", "commands.jsonl")


def ensure_private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, PRIVATE_DIR_MODE)
    except OSError:
        pass
    return path


def ensure_private_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()
    try:
        os.chmod(path, PRIVATE_FILE_MODE)
    except OSError:
        pass
    return path


def get_standard_data_dir() -> Path:
    return Path(GLib.get_user_data_dir()) / APP_DATA_DIRNAME


def migrate_legacy_data(legacy_dir: Path, target_dir: Path) -> None:
    if not legacy_dir.exists() or legacy_dir.resolve() == target_dir.resolve():
        return

    for filename in LEGACY_DATA_FILENAMES:
        source = legacy_dir / filename
        destination = target_dir / filename
        if not source.exists() or destination.exists():
            continue
        try:
            shutil.copy2(source, destination)
            ensure_private_file(destination)
        except OSError:
            continue


def get_data_dir() -> Path:
    override = os.environ.get("GLIPBOARD_DATA_DIR") or os.environ.get("MYCLIPBOARD_DATA_DIR")
    if override:
        data_dir = Path(override).expanduser()
    else:
        data_dir = get_standard_data_dir()
        migrate_legacy_data(PROJECT_DIR / ".glipboard-data", data_dir)
    ensure_private_dir(data_dir)
    return data_dir


class CommandChannel:
    def __init__(self, base_dir: Path) -> None:
        self.path = base_dir / "commands.jsonl"
        ensure_private_dir(self.path.parent)
        ensure_private_file(self.path)

    def write_command(self, command: str, payload: dict | None = None) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"command": command, "payload": payload or {}, "ts": time.time()}) + "\n")
        ensure_private_file(self.path)


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
