# MyClipboard

Clipboard manager per Pop!_OS, scritto in Python con GTK4/libadwaita.

## Avvio

```bash
npm start
```

Questo avvia:

- watcher clipboard via `wl-paste`
- finestra GTK principale
- helper tray separato via `AyatanaAppIndicator3`

## Requisiti principali

- Python 3
- GTK4 + libadwaita
- `wl-clipboard`
- `gir1.2-ayatanaappindicator3-0.1`

## Struttura

- `gtk_app.py`: applicazione principale GTK4
- `tray_helper.py`: helper tray separato GTK3/AppIndicator
- `scripts/wl-watch-event.sh`: framing degli eventi clipboard
- `legacy/electron/`: prototipo Electron mantenuto solo come riferimento storico
