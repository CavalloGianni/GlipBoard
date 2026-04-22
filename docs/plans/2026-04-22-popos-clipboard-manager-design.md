# MyClipboard V1 Design

## Goal

Build a lightweight clipboard manager for Pop!_OS that runs in the system tray, records recently copied text, and lets the user restore previous entries with a click.

## Product Scope

The first version is intentionally narrow:

- Target platform: Pop!_OS / Linux
- Session target: Wayland-first
- UI: tray menu only
- Data type: plain text only
- History size: 15 items
- Persistence: local JSON file

Out of scope for V1:

- image history
- binary content
- search UI
- favorites
- global shortcuts
- cloud sync
- Windows/macOS support

## Recommended Architecture

The application uses Electron only for desktop shell responsibilities:

- startup and lifecycle
- tray icon and context menu
- local state coordination
- clipboard restore actions

Clipboard capture is delegated to Linux-native tools instead of relying on Electron's clipboard polling.

### Wayland Capture Strategy

On Wayland, the app starts `wl-paste --watch` and passes a helper script as the command to run on each clipboard change.

Flow:

1. `wl-paste --watch` detects a new clipboard selection.
2. It runs the helper command and passes clipboard contents through stdin.
3. The helper script converts the event into a single JSON line.
4. The Electron main process receives the line, validates it, and updates history.
5. The tray menu is rebuilt to reflect the latest items.

This avoids brittle polling and better matches the Wayland security model.

## Data Model

The app stores clipboard history as a JSON document in the Electron user data directory.

Example structure:

```json
{
  "version": 1,
  "updatedAt": "2026-04-22T12:00:00.000Z",
  "items": [
    "Most recent copied text",
    "Previous copied text"
  ]
}
```

Rules:

- newest item first
- maximum 15 entries
- ignore empty text
- ignore oversized text beyond a safety limit
- de-duplicate identical entries by moving them to the top

## Tray Experience

The tray menu shows:

- app title
- current watcher state
- current session type
- clipboard history entries
- clear history action
- quit action

Each history item is displayed as a shortened one-line preview while the full text remains stored internally.

When a user clicks an item:

1. The text is written back to the active clipboard.
2. The item is moved to the top of history.
3. The tray menu is refreshed.

## Error Handling

The app must fail clearly rather than silently.

Cases:

- `wl-clipboard` missing: show a tray status message explaining that `wl-clipboard` is required.
- watcher process crash: log the failure, update tray status, and retry with backoff.
- corrupt history JSON: reset to an empty history without crashing.
- clipboard text too large or empty: ignore it.

## Test Plan

The V1 is considered successful when the following works on Pop!_OS Wayland:

1. App starts and tray icon appears.
2. Copying several distinct text snippets from different apps records them in order.
3. Restarting the app preserves the last 15 items.
4. Clicking a tray item restores it to the clipboard.
5. Missing `wl-clipboard` shows a clear degraded status instead of silent failure.

## Implementation Notes

The first implementation should favor correctness and observability over extra features:

- keep logic in the Electron main process
- use a small helper script for watcher event framing
- log watcher failures to the console
- avoid renderer windows until a richer UI is needed
