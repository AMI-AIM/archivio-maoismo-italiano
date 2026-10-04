# Convenzioni del codice (technical debt register)

Questo documento registra le **discordanze note** nel codice di AMI e le regole
da seguire per non aggravarle. Ogni voce indica lo stato attuale e la direzione
consigliata per i nuovi contributi.

> Ripristinato il 04/10/2026: era stato cancellato per errore dal commit
> automatico b7bee805 (30/09/2026, `git add -A` del Launcher). Aggiornati i
> punti 4, 6, 7 (font) e aggiunto il 9; le sezioni 2 e 3 riflettono lo stato
> di fine settembre e vanno riverificate rispetto a `DESIGN.md`.

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
`git_sync_pubblicazione()` esegue `pull --rebase --autostash → add → commit → push`.
**Dal 04/10/2026 l'add è selettivo**: solo i percorsi di `PERCORSI_PUBBLICATI`
(in testa a `Launcher.py`); i file modificati altrove vengono elencati a schermo
ma non committati. Per pubblicare un nuovo file in radice, aggiungerlo alla lista.
Il pull iniziale
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
Sorgente unica: `requirements.txt` (pandas, openpyxl, requests, Pillow, mkdocs,
mkdocs-material, lxml), con intervalli di versione bloccati sulla major
(04/10/2026). In particolare `mkdocs<2`: MkDocs 2.0 non è compatibile con
Material for MkDocs. Per aggiornare una dipendenza alla major successiva,
alzare il limite e verificare il sito in locale prima di pubblicare.
**Pillow È una dipendenza** (la scelta di settembre è stata superata):
`core/miniature.py` la usa per generare le miniature WebP delle copertine
scaricate da Internet Archive; se manca, la funzione degrada senza errori
ma le miniature non vengono prodotte. L'avatar `placeholder.webp` resta
invece un asset statico in `assets/immagini/profili/`, copiato da
`sync_assets.py`. `lxml` serve alla validazione XSD di EAD3/EAC-CPF
(`core/ead_export.py`, schemi in `scripts/schemi/`).
La CI installa da requirements.txt (`pip install -r`, deploy.yml).

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

File attuali (ott. 2026): `fraunces-variable`, `fraunces-400-italic`,
`archivo-variable`, `courier-prime-400/400-italic/700`; `fonts.css` è caricato
solo da `overrides/main.html`. Lo script `fonti_locali.py` citato in passato
non è più nel repository: per cambiare font sostituire a mano i woff2 e
aggiornare `fonts.css`. `sync_assets.py` copiare
`fonts/` in `build/` e fallisce se `fonts.css` o i woff2 mancano.

## 9. Export CSV dei dati e messaggi di commit
`scripts/core/export_dati.py`, chiamato dal Launcher subito dopo la
validazione, esporta ogni foglio di `data/dati.xlsx` in `data/export/<foglio>.csv`
(UTF-8 con BOM, apribili in Excel). Scopo: cronologia leggibile riga per riga
su GitHub (l'xlsx è binario) e copia dei dati in formato aperto.
- I CSV sono **derivati**: non modificarli a mano, la fonte resta l'xlsx.
- Il confronto con la versione in HEAD (chiave = prima colonna del foglio)
  produce il messaggio di commit, es. `Dati: Catalogo +2 ~1, Persone -1`,
  con l'elenco degli ID nel corpo.
- La CI non usa i CSV: la generazione del sito legge sempre l'xlsx.
- `.gitattributes` (`* text=auto`) normalizza i fine riga: nel repository LF,
  su Windows CRLF.

## 10. Lettura dei dati: `core/dati.py` (ott. 2026)
Tutti gli script leggono `dati.xlsx` con `leggi_foglio('Catalogo')` (o un
altro foglio): il file viene letto una sola volta per processo, ogni cella è
testo (`dtype=str`, vuoti = `''`), le colonne sono ripulite dagli spazi e,
di default, in minuscolo (`colonne='originali'` per averle come in Excel).
- Regola: **mai più `pd.read_excel` negli script**; usare `leggi_foglio`.
- Un foglio mancante solleva `ErroreDati` (prima alcuni moduli restituivano
  in silenzio un DataFrame vuoto e il sito usciva senza dati o senza link).
- Ogni chiamata restituisce una copia: modificarla non tocca gli altri moduli.
- Verificato al momento dell'introduzione: il sito generato è identico byte
  per byte a quello prodotto dalla versione precedente.

## 11. Errori e avvisi: `core/esito.py` (ott. 2026)
- **ERRORE** = sito rotto o incompleto: lo script esce con codice 1, il
  Launcher non pubblica, GitHub Actions fallisce. **AVVISO** = da sistemare,
  non blocca.
- Negli script: `sys.exit(esito.esegui_script('nome', main))` come punto
  d'ingresso; nelle fasi `esito.passo("descrizione", funzione, ...,
  bloccante=True/False)`; nei moduli `esito.avviso(...)` / `esito.errore(...)`.
  Non usare più `print("[WARN] ...")`: un avviso stampato e basta si perde.
- Classificazione in `generatore.py`: bloccanti schede, indice, JSON di
  ricerca, home, caricamento dati; non bloccanti EAD3/EAC-CPF (anche XML non
  valido rispetto allo schema), scheda raccolta, sitemap, ottimizzazione,
  cache. Le miniature non scaricabili sono un avviso.
- Riepilogo: ogni script aggiunge le sue voci a `.riepilogo-build.json`
  (escluso da Git); il Launcher lo azzera all'avvio e lo stampa prima di
  pubblicare. `python -m scripts.core.esito` mostra quello dell'ultima
  esecuzione. Su GitHub Actions le voci finiscono anche nel riepilogo del run.

## 12. Validazione: `core/validator.py` (riscritto ott. 2026)
Ogni problema riporta foglio, riga di Excel e colonna. Livelli: ERRORE
(blocca), AVVISO, NOTA (informazione, es. nomi citati senza scheda, che per
scelta restano senza link). Controlli principali:
- tutti i fogli: presenza dei fogli e delle colonne attese
  (`COLONNE_ATTESE`), testi provvisori (TODO, DA FARE, ??) fuori dalle date;
- Catalogo: ID unici e nel formato AMI-0001, titolo, tipo, livello, data
  riconoscibile, Data_normalizzata ISO e coerente con Data, URL di Internet
  Archive (e item non ripetuti), immagine per ogni percorso, nomi di autore
  e organizzazione con scheda, forme varianti usate al posto della forma
  autorizzata;
- Persone/Organizzazioni: ID AMI-P-/AMI-O-, nomi unici, indirizzi di pagina
  non in conflitto, estremi cronologici (1968, 196?, ????) e loro ordine,
  file immagine esistente, Wikidata/VIAF ben formati;
- Relazioni: ID esistenti, nome coerente con la scheda, ID mancante per
  entità che una scheda ce l'hanno, categoria ISAAR, formato delle date,
  relazioni ripetute;
- Raccolta: codici ISAD ben formati e non ripetuti.
Se Persone o Organizzazioni hanno problemi strutturali, i controlli
incrociati si saltano (eviterebbero centinaia di falsi allarmi).
Solo controllo dei dati, senza generare nulla: `python -m scripts.core.validator`.
