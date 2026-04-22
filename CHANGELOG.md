# Changelog

Tutte le modifiche rilevanti di GlipBoard saranno documentate in questo file.

## [0.1.1] - 2026-04-22

Miglioramento di compatibilita per ambienti Ubuntu/X11.

### Changed

- aggiunto supporto clipboard tramite `xclip` per sessioni X11
- mantenuto `wl-clipboard` come backend principale per Wayland
- migliorata la rilevazione automatica del backend clipboard disponibile
- aggiornato il packaging `.deb` per includere `xclip` tra le dipendenze

### Notes

- questa release nasce per migliorare il comportamento su Ubuntu oltre a Pop!_OS
- il warning `_apt` durante `apt install ./file.deb` non e la causa del problema clipboard
- la compatibilita Wayland resta il percorso principale gia testato su Pop!_OS

## [0.1.0] - 2026-04-22

Prima release pubblica del progetto.

### Added

- applicazione desktop GTK4/libadwaita per Pop!_OS
- cronologia dei testi copiati con limite configurabile
- ripristino rapido di un elemento della cronologia con un clic
- tray helper separato con accesso rapido alla finestra e agli ultimi elementi
- installazione desktop locale tramite script
- supporto a icona personalizzata del progetto

### Notes

- il progetto e pensato prima di tutto per Pop!_OS in ambiente Wayland
- lo stato attuale e stabile per uso personale e base pubblica iniziale
