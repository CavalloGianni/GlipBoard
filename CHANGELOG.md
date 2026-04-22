# Changelog

Tutte le modifiche rilevanti di GlipBoard saranno documentate in questo file.

## [0.1.0] - 2026-04-22

Prima release pubblica del progetto.

### Added

- applicazione desktop GTK4/libadwaita per Pop!_OS
- cronologia dei testi copiati con limite configurabile
- ripristino rapido di un elemento della cronologia con un clic
- tray helper separato con accesso rapido alla finestra e agli ultimi elementi
- supporto clipboard Wayland tramite `wl-clipboard`
- supporto clipboard X11 tramite `xclip`
- rilevazione automatica del backend clipboard disponibile
- installazione desktop locale tramite script
- pacchetto `.deb` installabile per uso desktop
- supporto a icona personalizzata del progetto
- avviso privacy nell'interfaccia e documentazione aggiornata

### Changed

- rimossa stampa nel terminale del testo copiato dagli appunti
- storage locale spostato sul path standard utente `~/.local/share/glipboard/`
- migrazione automatica dati compatibili da vecchie cartelle locali `.glipboard-data/`
- permessi storage locale irrigiditi per maggiore privacy

### Notes

- release pubblica iniziale consigliata per GlipBoard
- app salva cronologia solo in locale sul PC dell'utente
- GlipBoard non deve essere usato come archivio sicuro per password o segreti
