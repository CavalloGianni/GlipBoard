# GlipBoard

GlipBoard e un clipboard manager desktop per Pop!_OS.

L'app salva la cronologia dei testi copiati, ti permette di rivederli in una finestra semplice e di ricopiarli con un clic quando ti servono di nuovo.

![Logo GlipBoard](logo.2816x1536.png)

## Cosa fa

- monitora i testi copiati in ambiente Wayland
- mantiene una cronologia locale degli ultimi elementi copiati
- permette di ricopiare rapidamente un elemento dalla lista
- offre una finestra principale GTK4 stabile
- integra una tray come scorciatoia pratica, senza dipendere solo da quella
- supporta impostazioni base come numero massimo di elementi e avvio dell'interfaccia

## Stack del progetto

- Python 3
- GTK4 + libadwaita
- `wl-clipboard`
- `AyatanaAppIndicator3`

## Requisiti su Pop!_OS

Installa i pacchetti necessari:

```bash
sudo apt update
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 wl-clipboard gir1.2-ayatanaappindicator3-0.1
```

Se usi la tray su GNOME/Pop!_OS, assicurati anche di avere il supporto AppIndicator attivo.

## Avvio in sviluppo

Dal repository:

```bash
npm start
```

Questo comando avvia:

- la finestra principale GTK
- il watcher della clipboard basato su `wl-paste`
- il processo helper della tray

## Installazione locale

Per aggiungere GlipBoard alle applicazioni del tuo utente:

```bash
chmod +x scripts/install-local.sh scripts/uninstall-local.sh
./scripts/install-local.sh
```

L'installazione crea:

- il launcher desktop in `~/.local/share/applications/glipboard.desktop`
- lo script di avvio in `~/.local/share/glipboard/run-glipboard.sh`
- il riferimento all'icona `logo.2816x1536.png`

Per rimuovere l'installazione locale:

```bash
./scripts/uninstall-local.sh
```

Per reinstallare:

```bash
./scripts/uninstall-local.sh
./scripts/install-local.sh
```

## Come si usa

1. Avvia GlipBoard.
2. Copia normalmente del testo nel sistema.
3. Apri la finestra principale o usa la tray.
4. Seleziona un elemento della cronologia per copiarlo di nuovo negli appunti.

## Screenshot

Gli screenshot ufficiali dell'app saranno aggiunti in `docs/screenshots/`.

Suggerimento per la repository:

- una schermata della finestra principale
- una schermata della tray
- una schermata delle impostazioni

## Dati locali

GlipBoard salva i dati dell'app nella cartella locale:

```text
.glipboard-data/
```

Qui vengono conservati cronologia e impostazioni locali.

## Struttura del progetto

- `gtk_app.py`: applicazione principale GTK4/libadwaita
- `tray_helper.py`: helper tray separato basato su AppIndicator
- `scripts/install-local.sh`: installazione desktop locale
- `scripts/uninstall-local.sh`: rimozione installazione locale
- `scripts/wl-watch-event.sh`: gestione eventi clipboard via `wl-paste`

## Stato del progetto

Il progetto e gia utilizzabile su Pop!_OS ed e orientato a un uso personale reale, con l'idea di essere rifinito e reso sempre piu pronto per la pubblicazione.

## Prima release pubblica

La prima release pubblica preparata per il repository e `v0.1.0`.

Documenti utili:

- `CHANGELOG.md`
- `docs/releases/0.1.0.md`

## Roadmap iniziale

- migliorare ancora la presentazione della repository
- preparare una prima release pubblica
- valutare un pacchetto `.deb` per installazione piu semplice

## Repository

Repository GitHub:

`https://github.com/CavalloGianni/GlipBoard`
