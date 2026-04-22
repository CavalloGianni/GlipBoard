# GitHub Release Checklist: v0.1.0

Questa checklist serve per pubblicare la prima release GitHub di GlipBoard con il file `.deb`.

## Prima di pubblicare

- verifica che il branch `main` sia aggiornato su GitHub
- verifica che il file `dist/glipboard_0.1.0_all.deb` esista
- verifica che `package.json` riporti la versione `0.1.0`
- verifica che `CHANGELOG.md` e `docs/releases/0.1.0.md` siano aggiornati

## Tag Git

Se non esiste ancora il tag:

```bash
git tag -a v0.1.0 -m "GlipBoard v0.1.0"
git push origin v0.1.0
```

## Release GitHub

Nella repository GitHub:

1. apri la sezione `Releases`
2. premi `Draft a new release`
3. scegli il tag `v0.1.0`
4. usa come titolo `GlipBoard v0.1.0`
5. copia il contenuto principale da `docs/releases/0.1.0.md`
6. allega il file `dist/glipboard_0.1.0_all.deb`
7. pubblica la release

## Test da utente finale

Dopo la pubblicazione:

1. apri la pagina Releases come utente normale
2. scarica `glipboard_0.1.0_all.deb`
3. installa con:

```bash
sudo apt install ./glipboard_0.1.0_all.deb
```

4. verifica:

- presenza dell'app tra le applicazioni
- icona corretta
- apertura finestra principale
- funzionamento tray
- salvataggio cronologia in `~/.local/share/glipboard/`
