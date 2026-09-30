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

## 2. Stile CSS — due fonti (dopo la migrazione)
1. Fogli in `assets/stylesheets/*.css` (token `--ami-*`): extra.css,
   documenti.css, galleria.css, soggetti.css, soggetti-indice.css e i nuovi
   **home.css**, **archivio.css** e **argomenti.css** (migrati dai blocchi
   `<style>` inline di `core/home.py`, `core/archivio.py` e `argomenti.py`,
   set. 2026). Gli stili del footer sono migrati da
   `overrides/partials/footer.html` a fondo `extra.css`. Sono asset statici
   versionati, modificabili a mano; `sync_assets.py` li copia in `build/` e
   verifica che home.css/archivio.css/argomenti.css esistano (fallisce se
   mancano).
   Canali di caricamento: extra/documenti/galleria via `extra_css` di
   mkdocs.yml; home.css/archivio.css/soggetti.css/argomenti.css via `<link>`
   nel markdown generato (in coda alla pagina, per conservare la cascata
   post-extra.css).
2. Stili `style="..."` direttamente nell'HTML generato (banner, bottoni):
   residui storici, da migrare solo insieme alle regole `[style]` correlate.
Decisioni prese (set. 2026):
- **Solo light mode**: il tema scuro MkDocs slate e' abbandonato; `mkdocs.yml`
  fissa `scheme: default` senza toggle e i selettori slate sono stati rimossi
  da `extra.css`. Non reintrodurli.
- **Rosso brand = `#b71c1c`** ovunque (hard-coded in `home.py`, `404.html`,
  `galleria.css`); `palette.primary: red` di MkDocs resta solo per i componenti
  nativi del tema.
Problemi aperti (rinviati):
- home.css duplica ancora alcune sezioni di `extra.css` con valori divergenti
  (es. `.banner-content p[style]` 0.85rem vs 0.8rem in `extra.css:469`): ora
  il duplicato vive nei due file invece che inline, ma la cascata e' invariata
  (home.css arriva dopo). Da consolidare con confronto visivo.
- ~~Blocchi `<style>` superstiti~~: **esauriti** (ott. 2026). Nessuno script
  generatore ne template `overrides/` contiene piu' blocchi `<style>`; lo
  stile inline residuo e' solo negli attributi `style="..."` dell'HTML
  generato (banner hero, pannelli display:none) — vedi punto 2 sopra.
### 2.1 Scala tipografica unificata (token `--ami-font-size-*`)
Definita in `extra.css` nel blocco `:root`. Tutti i CSS custom usano i token,
non valori grezzi rem/px:
- font-size: xs 0.75 · sm 0.875 · base 1 · md 1.125 · lg 1.25 · xl 1.5 · 2xl 2 · 3xl 2.5 (rem)
- line-height: tight 1.2 · snug 1.35 · normal 1.5 · relaxed 1.6
- letter-spacing: tighter -0.02 · tight -0.01 · normal 0 · wide 0.03 · wider 0.05 (em)
Migrazione completata ott. 2026 su extra/home/archivio/argomenti/documenti/
soggetti/soggetti-indice/galleria. Valori fuori scala arrotondati al token piu'
vicino (es. 0.95→md, 0.8→sm, 0.65→xs): differenza ≤ 2px, da verificare visivamente.
Eccezioni deliberate NON tokenizzate: display enormi di argomenti.css (5.5rem,
4rem), `line-height: 1`/`2` strutturali, px nei componenti nativi del tema.
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

### 7. Font: self-hosted, niente Google Fonts a runtime (anti-FOUT)

I font (Fraunces, Archivo, Courier Prime) sono serviti in locale da
`assets/fonts/*.woff2` + `assets/stylesheets/fonts.css`, caricati nel
`<head>` di `overrides/main.html`. Vietato reintrodurre link a
`fonts.googleapis.com`/`fonts.gstatic.com`: il CSS remoto e' render-blocking
e causava il FOUT (testo Georgia -> ridisegno al carico dei woff2).

Strategia adottata (richiesta del manutentore: il font reale deve comparire
SUBITO): `font-display: block` + preload dei tre file piu' critici
(fraunces-900 titolo hero, fraunces-400 corpo, archivo-500 UI). Con i font
self-hosted e preloaded il blocco iniziale dura pochi ms (stesso server,
file piccoli) e non c'e' mai ridisegnamento a testo gia' visibile: niente
FOUT e font corretto dalla prima visita. Nota: `optional` era la strategia
precedente (font reale solo dalla seconda visita) - NON ripristinarla senza
nuova decisione del manutentore.

Per cambiare pesi/famiglie: modificare `API_URL` in `scripts/fonti_locali.py`
ed eseguirlo (`--force` per riscrivere i file). `sync_assets.py` copiare
`fonts/` in `build/` e fallisce se `fonts.css` o i woff2 mancano.
