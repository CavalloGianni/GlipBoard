from __future__ import annotations

import base64
import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk


APP_ID = "com.gianni.GlipBoard"
APP_NAME = "GlipBoard"
DEFAULT_MAX_HISTORY_ITEMS = 15
MAX_TEXT_LENGTH = 50_000
WATCHER_ARGS = ["wl-paste", "--type", "text", "--watch", "sh", "scripts/wl-watch-event.sh"]
PROJECT_DIR = Path(__file__).resolve().parent
APP_ICON_PATH = (
    PROJECT_DIR / "logo.2816x1536.png"
    if (PROJECT_DIR / "logo.2816x1536.png").exists()
    else PROJECT_DIR / "logo.png"
)


def normalize_text(text: str) -> str:
    return str(text).replace("\r\n", "\n").replace("\r", "\n")


def summarize_text(text: str, max_length: int = 90) -> str:
    single_line = " ".join(text.split())
    if not single_line:
        return "(Testo vuoto)"
    if len(single_line) <= max_length:
        return single_line
    return f"{single_line[: max_length - 3]}..."


def is_useful_text(text: str) -> bool:
    return bool(text and text.strip() and len(text) <= MAX_TEXT_LENGTH)


def command_exists(command: str, args: list[str] | None = None) -> bool:
    test_args = args or ["--version"]
    try:
        result = subprocess.run([command, *test_args], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return False
    return result.returncode == 0


def get_data_dir() -> Path:
    override = GLib.getenv("GLIPBOARD_DATA_DIR") or GLib.getenv("MYCLIPBOARD_DATA_DIR")
    if override:
        data_dir = Path(override).expanduser()
    else:
        data_dir = PROJECT_DIR / ".glipboard-data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@dataclass
class AppSettings:
    max_items: int = DEFAULT_MAX_HISTORY_ITEMS
    show_window_on_startup: bool = True
    autostart_enabled: bool = False


@dataclass
class AppState:
    items: list[str]
    status: str = "Pronto"


class HistoryStore:
    def __init__(self, base_dir: Path) -> None:
        self.path = base_dir / "clipboard-history.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self, max_items: int) -> list[str]:
        if not self.path.exists():
            return []

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

        items = payload.get("items", [])
        if not isinstance(items, list):
            return []

        return [
            normalize_text(item)
            for item in items
            if isinstance(item, str) and is_useful_text(normalize_text(item))
        ][:max_items]

    def save(self, items: list[str], max_items: int) -> None:
        payload = {
            "version": 1,
            "updatedAt": GLib.DateTime.new_now_utc().format_iso8601(),
            "items": items[:max_items],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class SettingsStore:
    def __init__(self, base_dir: Path) -> None:
        self.path = base_dir / "settings.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return AppSettings()

        max_items = payload.get("max_items", DEFAULT_MAX_HISTORY_ITEMS)
        show_window_on_startup = payload.get("show_window_on_startup", True)
        autostart_enabled = payload.get("autostart_enabled", False)

        if not isinstance(max_items, int):
            max_items = DEFAULT_MAX_HISTORY_ITEMS
        max_items = min(max(max_items, 5), 100)

        if not isinstance(show_window_on_startup, bool):
            show_window_on_startup = True
        if not isinstance(autostart_enabled, bool):
            autostart_enabled = False

        return AppSettings(
            max_items=max_items,
            show_window_on_startup=show_window_on_startup,
            autostart_enabled=autostart_enabled,
        )

    def save(self, settings: AppSettings) -> None:
        payload = {
            "version": 1,
            "updatedAt": GLib.DateTime.new_now_utc().format_iso8601(),
            "max_items": settings.max_items,
            "show_window_on_startup": settings.show_window_on_startup,
            "autostart_enabled": settings.autostart_enabled,
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class AutostartManager:
    def __init__(self, project_dir: Path) -> None:
        config_home = Path(GLib.getenv("XDG_CONFIG_HOME") or Path.home() / ".config")
        self.autostart_dir = config_home / "autostart"
        self.desktop_file = self.autostart_dir / "glipboard.desktop"
        self.project_dir = project_dir

    def apply(self, enabled: bool) -> None:
        self.autostart_dir.mkdir(parents=True, exist_ok=True)
        if enabled:
            self.desktop_file.write_text(self._desktop_entry(), encoding="utf-8")
        elif self.desktop_file.exists():
            self.desktop_file.unlink()

    def _desktop_entry(self) -> str:
        exec_path = f"/usr/bin/env bash -lc 'cd \"{self.project_dir}\" && python3 gtk_app.py'"
        icon_line = f"Icon={APP_ICON_PATH}" if APP_ICON_PATH.exists() else ""
        lines = [
            "[Desktop Entry]",
            "Type=Application",
            "Version=1.0",
            f"Name={APP_NAME}",
            "Comment=Clipboard manager for Pop!_OS",
            f"Exec={exec_path}",
            "Terminal=false",
            "Categories=Utility;",
            "X-GNOME-Autostart-enabled=true",
        ]
        if icon_line:
            lines.append(icon_line)
        return "\n".join(
            lines
        ) + "\n"


class CommandChannel:
    def __init__(self, base_dir: Path) -> None:
        self.path = base_dir / "commands.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self._read_position = self.path.stat().st_size

    def write_command(self, command: str, payload: dict | None = None) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"command": command, "payload": payload or {}, "ts": time.time()}) + "\n")

    def read_new_commands(self) -> list[tuple[str, dict]]:
        if not self.path.exists():
            return []

        commands: list[tuple[str, dict]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            handle.seek(self._read_position)
            for line in handle:
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                command = payload.get("command")
                data = payload.get("payload", {})
                if isinstance(command, str):
                    commands.append((command, data if isinstance(data, dict) else {}))
            self._read_position = handle.tell()
        return commands


class ClipboardWatcher:
    def __init__(self, on_text, on_error) -> None:
        self._on_text = on_text
        self._on_error = on_error
        self._process: subprocess.Popen[str] | None = None
        self._stdout_thread: threading.Thread | None = None
        self._stderr_thread: threading.Thread | None = None

    def start(self) -> None:
        try:
            self._process = subprocess.Popen(
                WATCHER_ARGS,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                cwd=Path(__file__).resolve().parent,
                bufsize=1,
            )
        except FileNotFoundError:
            GLib.idle_add(self._on_error, "Dipendenza mancante: installa wl-clipboard")
            return
        except OSError as error:
            GLib.idle_add(self._on_error, f"Errore watcher: {error}")
            return

        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stdout_thread.start()
        self._stderr_thread.start()

    def stop(self) -> None:
        if self._process and self._process.poll() is None:
            self._process.terminate()
        self._process = None

    def _read_stdout(self) -> None:
        if not self._process or not self._process.stdout:
            return

        for line in self._process.stdout:
            line = line.strip()
            if not line:
                continue

            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue

            if payload.get("state") != "data":
                continue

            encoded = payload.get("textBase64", "")
            try:
                text = base64.b64decode(encoded).decode("utf-8")
            except (ValueError, UnicodeDecodeError):
                continue

            GLib.idle_add(self._on_text, text)

    def _read_stderr(self) -> None:
        if not self._process or not self._process.stderr:
            return

        for line in self._process.stderr:
            message = line.strip()
            if message:
                GLib.idle_add(self._on_error, summarize_text(message, 120))


class TrayHelper:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.process: subprocess.Popen[str] | None = None

    def start(self) -> None:
        if not command_exists("python3"):
            return

        try:
            self.process = subprocess.Popen(
                ["python3", "tray_helper.py"],
                cwd=Path(__file__).resolve().parent,
                env={
                    **os.environ,
                    "GLIPBOARD_DATA_DIR": str(self.base_dir),
                    "MYCLIPBOARD_DATA_DIR": str(self.base_dir),
                },
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        except OSError:
            self.process = None

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.process = None


class HistoryRow(Gtk.ListBoxRow):
    def __init__(self, text: str, on_activate) -> None:
        super().__init__()
        self.text = text

        button = Gtk.Button(css_classes=["flat"])
        button.connect("clicked", lambda *_args: on_activate(self.text))

        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        outer.set_margin_top(10)
        outer.set_margin_bottom(10)
        outer.set_margin_start(12)
        outer.set_margin_end(12)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        body.set_hexpand(True)

        title = Gtk.Label(label=summarize_text(text, 80), xalign=0)
        title.add_css_class("heading")

        preview = Gtk.Label(label=text, wrap=True, wrap_mode=2, xalign=0)
        preview.add_css_class("dim-label")

        body.append(title)
        body.append(preview)

        icon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        icon_box.add_css_class("card")
        icon_box.set_valign(Gtk.Align.CENTER)

        icon = Gtk.Image.new_from_icon_name("edit-copy-symbolic")
        icon.set_pixel_size(16)
        icon.set_margin_top(8)
        icon.set_margin_bottom(8)
        icon.set_margin_start(8)
        icon.set_margin_end(8)
        icon_box.append(icon)

        outer.append(body)
        outer.append(icon_box)
        button.set_child(outer)
        self.set_child(button)


class PreferencesDialog(Adw.PreferencesDialog):
    def __init__(self, app: "MyClipboardApp", parent: Gtk.Window) -> None:
        super().__init__()
        self.app_ref = app
        self.set_title("Preferenze")

        page = Adw.PreferencesPage()
        self.add(page)

        group = Adw.PreferencesGroup(
            title="Generale",
            description="Imposta il comportamento di base della cronologia.",
        )
        page.add(group)

        self.max_items_row = Adw.SpinRow.new_with_range(5, 100, 1)
        self.max_items_row.set_title("Numero massimo elementi salvati")
        self.max_items_row.set_subtitle("Lo storico verrà limitato a questo numero di elementi.")
        self.max_items_row.set_value(self.app_ref.settings.max_items)
        self.max_items_row.connect("notify::value", self._on_max_items_changed)
        group.add(self.max_items_row)

        self.show_on_startup_row = Adw.SwitchRow()
        self.show_on_startup_row.set_title("Mostra finestra all'avvio")
        self.show_on_startup_row.set_subtitle("Se disattivato, l'app parte in background e non mostra subito la finestra.")
        self.show_on_startup_row.set_active(self.app_ref.settings.show_window_on_startup)
        self.show_on_startup_row.connect("notify::active", self._on_show_on_startup_changed)
        group.add(self.show_on_startup_row)

        self.autostart_row = Adw.SwitchRow()
        self.autostart_row.set_title("Avvia automaticamente con il sistema")
        self.autostart_row.set_subtitle("Crea o rimuove l'avvio automatico di GlipBoard in Pop!_OS.")
        self.autostart_row.set_active(self.app_ref.settings.autostart_enabled)
        self.autostart_row.connect("notify::active", self._on_autostart_changed)
        group.add(self.autostart_row)

    def _on_max_items_changed(self, row, _pspec) -> None:
        self.app_ref.update_max_items(int(row.get_value()))

    def _on_show_on_startup_changed(self, row, _pspec) -> None:
        self.app_ref.update_show_window_on_startup(row.get_active())

    def _on_autostart_changed(self, row, _pspec) -> None:
        self.app_ref.update_autostart(row.get_active())


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: "MyClipboardApp") -> None:
        super().__init__(application=app, title=APP_NAME)
        self.app_ref = app
        self.set_default_size(560, 680)

        self.connect("close-request", self._on_close_request)

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        toolbar = Adw.ToolbarView()
        self.toast_overlay.set_child(toolbar)

        header = Adw.HeaderBar()

        title_stack = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title = Gtk.Label(label=APP_NAME)
        title.add_css_class("title-2")
        subtitle = Gtk.Label(label="Cronologia dei testi copiati", xalign=0)
        subtitle.add_css_class("dim-label")
        title_stack.append(title)
        title_stack.append(subtitle)
        header.set_title_widget(title_stack)

        prefs_button = Gtk.Button(icon_name="emblem-system-symbolic")
        prefs_button.set_tooltip_text("Preferenze")
        prefs_button.connect("clicked", lambda *_args: self.app_ref.show_preferences(self))

        clear_button = Gtk.Button(icon_name="user-trash-symbolic")
        clear_button.set_tooltip_text("Pulisci cronologia")
        clear_button.connect("clicked", lambda *_args: self.app_ref.clear_history())

        header.pack_end(clear_button)
        header.pack_end(prefs_button)

        toolbar.add_top_bar(header)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        content.set_margin_start(16)
        content.set_margin_end(16)
        toolbar.set_content(content)

        status_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        status_card.add_css_class("card")
        status_card.set_margin_top(4)
        status_card.set_margin_bottom(4)
        status_card.set_margin_start(4)
        status_card.set_margin_end(4)

        self.count_label = Gtk.Label(xalign=0)
        self.count_label.add_css_class("heading")
        self.count_label.set_margin_top(12)
        self.count_label.set_margin_start(12)
        self.count_label.set_margin_end(12)

        self.status_label = Gtk.Label(xalign=0)
        self.status_label.add_css_class("dim-label")
        self.status_label.set_margin_bottom(12)
        self.status_label.set_margin_start(12)
        self.status_label.set_margin_end(12)

        status_card.append(self.count_label)
        status_card.append(self.status_label)
        content.append(status_card)

        self.list_box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.list_box.add_css_class("boxed-list")

        scrolled = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(self.list_box)
        content.append(scrolled)

        self.empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.empty_box.add_css_class("card")
        self.empty_box.set_margin_top(12)
        self.empty_box.set_margin_bottom(12)
        self.empty_box.set_margin_start(12)
        self.empty_box.set_margin_end(12)

        empty_title = Gtk.Label(label="Cronologia vuota")
        empty_title.add_css_class("title-3")
        empty_title.set_margin_top(18)
        empty_title.set_margin_start(18)
        empty_title.set_margin_end(18)

        empty_text = Gtk.Label(
            label="Copia un testo da un'altra app e comparirà qui automaticamente.",
            wrap=True,
            wrap_mode=2,
            xalign=0,
        )
        empty_text.add_css_class("dim-label")
        empty_text.set_margin_bottom(18)
        empty_text.set_margin_start(18)
        empty_text.set_margin_end(18)

        self.empty_box.append(empty_title)
        self.empty_box.append(empty_text)
        content.append(self.empty_box)

        self.refresh()

    def _on_close_request(self, _window) -> bool:
        self.hide()
        if self.app_ref:
            self.app_ref.set_status("App in background")
        return True

    def refresh(self) -> None:
        state = self.app_ref.state
        settings = self.app_ref.settings
        self.count_label.set_label(f"Elementi copiati: {len(state.items)} di {settings.max_items}")
        self.status_label.set_label(state.status)

        child = self.list_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.list_box.remove(child)
            child = next_child

        for text in state.items:
            self.list_box.append(HistoryRow(text, self.app_ref.restore_clipboard))

        has_items = len(state.items) > 0
        self.empty_box.set_visible(not has_items)
        self.list_box.set_visible(has_items)

    def show_toast(self, message: str) -> None:
        self.toast_overlay.add_toast(Adw.Toast(title=message))


class MyClipboardApp(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.data_dir = get_data_dir()
        self.project_dir = PROJECT_DIR
        self.history_store = HistoryStore(self.data_dir)
        self.settings_store = SettingsStore(self.data_dir)
        self.command_channel = CommandChannel(self.data_dir)
        self.tray_helper = TrayHelper(self.data_dir)
        self.autostart_manager = AutostartManager(self.project_dir)
        self.settings = self.settings_store.load()
        self.state = AppState(items=self.history_store.load(self.settings.max_items))
        self.window: MainWindow | None = None
        self.watcher: ClipboardWatcher | None = None
        self.preferences_dialog: PreferencesDialog | None = None
        self.last_text = self.state.items[0] if self.state.items else ""

    def do_activate(self) -> None:
        if not self.window:
            self.window = MainWindow(self)

        if self.settings.show_window_on_startup:
            self.window.present()

        if not self.watcher:
            self.start_services()

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)

        action = Gio.SimpleAction.new("show", None)
        action.connect("activate", lambda *_args: self.present_main_window())
        self.add_action(action)

        GLib.timeout_add(500, self.poll_commands)
        self.tray_helper.start()
        self.autostart_manager.apply(self.settings.autostart_enabled)

    def do_shutdown(self) -> None:
        if self.watcher:
            self.watcher.stop()
            self.watcher = None
        self.tray_helper.stop()
        Gio.Application.do_shutdown(self)

    def poll_commands(self) -> bool:
        for command, payload in self.command_channel.read_new_commands():
            if command == "show":
                self.present_main_window()
            elif command == "hide" and self.window:
                self.window.hide()
                self.set_status("App in background")
            elif command == "clear":
                self.clear_history()
            elif command == "copy":
                text = payload.get("text")
                if isinstance(text, str):
                    self.restore_clipboard(text)
            elif command == "quit":
                self.quit()
        return True

    def present_main_window(self) -> None:
        if not self.window:
            self.window = MainWindow(self)
        self.window.present()

    def start_services(self) -> None:
        if not command_exists("wl-paste") or not command_exists("wl-copy"):
            self.set_status("Dipendenza mancante: installa wl-clipboard")
            return

        self.set_status("Watcher clipboard attivo")
        self.watcher = ClipboardWatcher(self.handle_captured_text, self.handle_watcher_error)
        self.watcher.start()

    def set_status(self, message: str) -> None:
        self.state.status = message
        if self.window:
            self.window.refresh()

    def persist_history(self) -> None:
        self.history_store.save(self.state.items, self.settings.max_items)

    def trim_history_to_settings(self) -> None:
        self.state.items = self.state.items[: self.settings.max_items]
        if self.last_text not in self.state.items:
            self.last_text = self.state.items[0] if self.state.items else ""

    def update_max_items(self, value: int) -> None:
        self.settings.max_items = min(max(int(value), 5), 100)
        self.trim_history_to_settings()
        self.settings_store.save(self.settings)
        self.persist_history()
        self.set_status("Preferenze aggiornate")
        if self.window:
            self.window.show_toast("Numero massimo elementi aggiornato")

    def update_show_window_on_startup(self, enabled: bool) -> None:
        self.settings.show_window_on_startup = bool(enabled)
        self.settings_store.save(self.settings)
        self.set_status("Preferenze aggiornate")
        if self.window:
            self.window.show_toast("Preferenza di avvio aggiornata")

    def update_autostart(self, enabled: bool) -> None:
        self.settings.autostart_enabled = bool(enabled)
        self.settings_store.save(self.settings)
        try:
            self.autostart_manager.apply(self.settings.autostart_enabled)
            self.set_status("Preferenze aggiornate")
            if self.window:
                self.window.show_toast("Autostart aggiornato")
        except OSError as error:
            self.settings.autostart_enabled = not bool(enabled)
            self.settings_store.save(self.settings)
            self.set_status(f"Errore autostart: {error}")
            if self.window:
                self.window.show_toast("Errore nell'aggiornare l'autostart")

    def show_preferences(self, parent: Gtk.Window) -> None:
        self.preferences_dialog = PreferencesDialog(self, parent)
        self.preferences_dialog.present(parent)

    def handle_watcher_error(self, message: str) -> bool:
        self.set_status(message)
        return False

    def handle_captured_text(self, text: str) -> bool:
        normalized = normalize_text(text)
        if not is_useful_text(normalized):
            return False

        if normalized == self.last_text:
            return False

        self.last_text = normalized
        self.state.items = [item for item in self.state.items if item != normalized]
        self.state.items.insert(0, normalized)
        self.trim_history_to_settings()
        self.persist_history()
        self.set_status("Watcher clipboard attivo")
        print(f"Clipboard catturata: {summarize_text(normalized)}")
        return False

    def restore_clipboard(self, text: str) -> None:
        try:
            subprocess.run(["wl-copy", "--type", "text/plain"], input=text, text=True, check=True)
        except (OSError, subprocess.CalledProcessError) as error:
            self.set_status(f"Errore wl-copy: {error}")
            if self.window:
                self.window.show_toast("Errore nel ripristino degli appunti")
            return

        self.last_text = text
        self.state.items = [item for item in self.state.items if item != text]
        self.state.items.insert(0, text)
        self.trim_history_to_settings()
        self.persist_history()
        self.set_status("Testo copiato negli appunti")
        if self.window:
            self.window.show_toast("Copiato negli appunti")

    def clear_history(self) -> None:
        self.state.items = []
        self.last_text = ""
        self.persist_history()
        self.set_status("Cronologia svuotata")
        if self.window:
            self.window.show_toast("Cronologia pulita")


def main() -> int:
    try:
        app = MyClipboardApp()
        return app.run(None)
    except RuntimeError as error:
        print(f"Impossibile inizializzare GTK: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
