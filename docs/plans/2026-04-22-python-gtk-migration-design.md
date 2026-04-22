# MyClipboard Python GTK Migration Design

## Goal

Replace the Electron prototype with a Pop!_OS-first desktop application built in Python with GTK4 and libadwaita.

The new version should:

- store recently copied text entries
- restore an entry back to the clipboard with a click
- use a normal desktop window for the history UI
- keep tray support as a future extension rather than the only way to use the app

## Why Migrate

The Electron version hit repeated platform-level issues on Pop!_OS under Wayland and XWayland:

- unreliable foreground behavior for shortcut-triggered windows
- unstable popup rendering in Chromium/Electron on this environment
- repeated X11/XWayland presentation errors unrelated to the clipboard logic itself

The migration keeps the validated product behavior while replacing the unstable window shell.

## V1 Scope

The first GTK version intentionally focuses on the stable core:

- Python 3
- GTK4 + libadwaita
- Wayland-first clipboard capture through `wl-paste --watch`
- clipboard restore through `wl-copy`
- local JSON persistence
- normal application window with clickable clipboard history
- maximum 15 items

Out of scope for the first GTK implementation:

- configurable global shortcut
- favorites and search
- packaging and distribution

These remain planned but should not block delivery of a reliable core.

## Architecture

### Application Layer

An `Adw.Application` bootstraps the desktop app, creates the main window, loads persisted data, and starts the clipboard watcher.

### Clipboard Watcher

The app runs:

`wl-paste --type text --watch sh scripts/wl-watch-event.sh`

The helper script frames each clipboard change as a single JSON line. A Python watcher thread reads those lines and forwards decoded text back to the GTK main loop using `GLib.idle_add`.

### History Store

Clipboard entries are persisted in a JSON file under the user data directory.

Rules:

- newest first
- maximum 15 items
- skip empty items
- skip oversized items
- de-duplicate by moving existing entries to the top

### Main Window

The window is a normal libadwaita application window containing:

- header bar
- clipboard count label
- scrollable list of copied items
- clear action

Each list item is clickable. Clicking an item writes it back to the clipboard and shows a small confirmation toast.

## Error Handling

The app must fail clearly, not silently.

Cases:

- `wl-clipboard` missing: show a status message in the UI
- history file corrupt: recover with empty history
- watcher process exits: show degraded state and stop claiming success
- `wl-copy` failure: show a toast or status update instead of crashing

## Migration Plan

1. Add the GTK application entrypoint alongside the current Electron files.
2. Reuse the existing shell watcher helper script where possible.
3. Switch `npm start` to launch the GTK version for easier local testing.
4. Move the Electron prototype into a legacy area once GTK becomes the main implementation.
5. Add tray and shortcut support only after the GTK core is stable on Pop!_OS.

## Success Criteria

The GTK migration is successful when:

1. `npm start` launches the GTK app.
2. Copying text from other apps populates the history.
3. Restarting the app preserves the last 15 entries.
4. Clicking an entry writes it back to the clipboard.
5. The app runs without the Electron/XWayland window failures seen in the previous prototype.
