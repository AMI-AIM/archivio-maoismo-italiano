# Convenzioni del codice (technical debt register)

Questo documento registra le **discordanze note** nel codice di AMI e le regole
da seguire per non aggravarle. Ogni voce indica lo stato attuale e la direzione
consigliata per i nuovi contributi.

## 1. Percorsi degli asset (CSS/JS) — due idiomi convissuti
- Le pagine in **radice** (home, archivio) usano `site_path('...')`
  (`scripts/core/site_config.py`, URL derivati da `site_url` di `mkdocs.yml`).
- Le pagine in **sottocartella** usano il relativo `../stylesheets/...`
  (es. indici persone/organizzazioni in `persone.py:426`, `org.py:457`) oppure
  l'assoluto `site_path(...)` (schede singolo soggetto, `argomenti.py`).
- Regola: usare `site_path()` ogni volta che il generatore puo' importarlo;
  il `../` relativo e' tollerato solo dove il livello di profondita' e' fisso.
- Attenzione: `assets/stylesheets/documenti.css` e' caricato globalmente da
  `mkdocs.yml` (`extra_css`), mentre `soggetti.css` e `soggetti-indice.css`
  sono linkati esplicitamente dai generatori: quando si sposta una regola,
  verificare quale dei due canali la eredita.

## 2. Stile CSS — tre fonti
1. Token e layout in `assets/stylesheets/*.css` (variabili `--ami-*`).
2. Blocchi `<style>` inline nei generatori: `core/home.py` (~550 righe),
   `core/archivio.py` (~570), `argomenti.py`, `overrides/partials/footer.html`.
3. Stili `style="..."` direttamente nell'HTML generato (banner, bottoni).
Decisioni prese (set. 2026):
- **Solo light mode**: il tema scuro MkDocs slate e' abbandonato; `mkdocs.yml`
  fissa `scheme: default` senza toggle e i selettori slate sono stati rimossi
  da `extra.css`. Non reintrodurli.
- **Rosso brand = `#b71c1c`** ovunque (hard-coded in `home.py`, `404.html`,
  `galleria.css`); `palette.primary: red` di MkDocs resta solo per i componenti
  nativi del tema.
Problemi aperti (migrazione rinviata):
- Il blocco inline di home duplica sezioni di `extra.css` con valori divergenti
  (es. `.banner-content p[style] { font-size: 0.85rem }` inline vs `0.8rem` in
  `extra.css:469`; vince l'inline perche' successivo nel `<head>`).
Regola: nuovo CSS va in `assets/stylesheets/`, parametrizzato con `--ami-*`;
i blocchi inline vanno progressivamente migrati (la migrazione completa richiede
un confronto visivo pagina per pagina). Codice morto CSS rimosso: selettori mai
presenti nel markup generato (`.doc-thumbnail`, `.subject-avatar`,
`.archive-card`, `.skeleton-grid`, `.gallery-item`, utility aspect/w-*,
`.home-page`) — prima di aggiungere una regola, verificare che la classe esista
negli output dei generatori.

## 3. Frontend JavaScript
- Idiom misto: `getElementById` (archivio-filtri.js ~50 occorrenze) contro
  `querySelector` (galleria.js, lazy-loading.js). Preferire `querySelector`.
- Tutti gli script sono vanilla JS senza build step: niente minificazione.

## 4. Pipeline duplicata Launcher / CI
L'ordine degli script (`sync_assets → persone → org → generatore → argomenti → galleria`)
e' replicato in `Launcher.py` e in `.github/workflows/deploy.yml`. Modificare
entrambi sempre in coppia (oppure estrarre uno script unico invocato da entrambi).

**Aggiornamento 29/09/2026 — scelta: mantenere la duplicazione.** Un modulo
comune che invochi gli script funzionerebbe solo nel job di build, ma la CI ha
step separati con fallimento selettivo per fase (utile nei log di Actions);
inoltre la pipeline locale deve poter girare senza dipendenze da runner. La
coppia Launcher/deploy.yml resta quindi intenzionale: ogni modifica all'ordine
degli step va applicata a entrambi i file nello stesso commit. Il Launcher usa
gia` `sys.executable` (niente hardcoding `python`), quindi l'unica regola
operativa e' la coppia dei file.

### Pubblicazione git del Launcher
`git_sync_pubblicazione()` esegue `pull --rebase --autostash → add -A → commit → push`:
recupera i commit fatti altrove (es. merge GitHub) prima di spingere, evitando il
rifiuto non-fast-forward. Testato con remoto bare locale (storia divergente +
worktree sporco: rebase lineare, modifiche preservate, push ricevuto).

## 5. Date
Convenzione di data entry italiana `gg/mm/aaaa`. In `utils.formatta_data`
`%m/%d/%Y` esiste solo come fallback estremo dopo `%d/%m/%Y` (vedi commento in
`core/utils.py`). **Nota: il fallback `%m/%d/%Y` e' deprecato** — con la
priorita' attuale una data come "05/12/1970" viene sempre letta 5 dicembre;
le date anglofone vanno convertite in `gg/mm/aaaa` direttamente nel foglio.
Non aggiungere formati ambigui prima di questi.

## 6. Dipendenze Python
Sorgente unica: `requirements.txt` (pandas, openpyxl, requests, mkdocs-material).
**Pillow NON e' una dipendenza del progetto** (scelta del manutentore:
semplicita'). L'avatar `placeholder.webp` delle schede senza foto e' un asset
statico versionato in `assets/immagini/profili/`, copiato in `build/` da
`sync_assets.py`: nessun file immagine viene generato a runtime (in passato
`generatore.py` conteneva codice Pillow opzionale per crearlo se mancante —
rimosso; ora `verifica_placeholder_profili()` si limita a controllare che
l'asset esista). `requests` era usato ma non dichiarato: ora presente. La CI
installa i requisiti da requirements.txt (`pip install -r`, deploy.yml): se in
futuro il validatore o altri moduli core useranno nuove librerie, aggiornare
requirements.txt (non serve toccare deploy.yml, che legge il file).

### Versione Python
La CI fissa Python **3.12** (setup-python in deploy.yml). Richiesta minima
consigliata per l'ambiente locale: **>= 3.10**, coerente con la sintassi usata
(type hint moderni, f-string). Non ci sono pin espliciti altrove: se si introduce
un `.python-version` o constraint `python_requires`, aggiornare qui e nel README.

## 7. Naming IT/EN misto
Funzioni/pubblico in italiano (`formatta_data`, `scarica_descrizione_ia`),
moduli/meccanismi in inglese (`validator`, `cache_manager`, `json_optimizer`).
Non normalizzare ora (rischio regressioni > beneficio); mantenere coerenza
nel modulo che si tocca.

## 8. Documentazione CLI
Il riferimento completo dei comandi e' il docstring di `Launcher.py` e
`comandi.txt`. `README.md` elenca solo i casi d'uso principali: alla fine di
questa sezione c'e' il rimando. Aggiornare `comandi.txt` a ogni nuova opzione.
