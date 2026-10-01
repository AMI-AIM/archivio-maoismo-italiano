# Audit tecnico — Archivio del Maoismo Italiano

Data: 1 ottobre 2026 · Oggetto: sito pubblicato (branch `gh-pages`, build del 01/10/2026 17:30) + sorgenti `main` (`overrides/`, `assets/`, `scripts/core/`).
Metodo: lettura del codice, detector Impeccable, axe-core 4 (WCAG 2.0/2.1 A-AA + best practice) e Playwright/Chromium su 12 pagine tipo, a 1440×900 e 390×844 (viewport mobile emulato con touch).
Limite: dall'ambiente di test archive.org non era raggiungibile; copertine, embed e banner "Internet Archive instabile" visibili negli screenshot dipendono da questo e non sono stati contati come bug, salvo dove rivelano un problema di robustezza reale.

## Punteggio

| # | Dimensione | Voto | Problema principale |
|---|---|---|---|
| 1 | Accessibilità | 2 | Focus invisibile su ricerca hero e footer; dropdown e hamburger senza semantica corretta |
| 2 | Performance | 2 | Due font precaricati inesistenti (404 su ogni pagina); immagini sovradimensionate e senza dimensioni |
| 3 | Responsive | 3 | Nessun overflow su mobile; target touch piccoli in paginazione, alfabeto, azioni scheda |
| 4 | Theming | 2 | Token tipografici solidi, ma ~110 colori hard-coded e un secondo sistema di token in galleria |
| 5 | Integrità implementativa | 2 | Il sistema tipografico dichiarato non arriva mai al browser |
| **Totale** | | **11/20** | **Accettabile, con interventi significativi** |

## Verdetto sull'integrità implementativa: NON SUPERATO (di poco)

L'identità del sito è coerente e specifica: rosso #b71c1c, Fraunces e Archivo, Courier Prime per i metadati, un'iconografia d'archivio. **Però non viene renderizzata.** `fonts.css` dichiara `fraunces-variable.woff2` e `archivo-variable.woff2`, e `main.html` li precarica, ma in `assets/fonts/` e nel sito pubblicato ci sono solo i file statici (`fraunces-400-normal`, `archivo-600-normal`, ecc.). Il risultato, verificato con `document.fonts`, è questo:

- `Fraunces 100 900 normal → error`, `Archivo 100 900 normal → error`, `Fraunces 400 italic → loaded`
- tutto il tondo cade su Georgia, tutte le etichette su Arial, mentre i corsivi (date di vita, sottotitoli) sono in vero Fraunces: due serif diversi nella stessa card (es. "Mao Zedong / *1893 – 1976*" su /persone/).

Il commento in testa a `fonts.css` descrive un sistema che non esiste nei file. Il resto del verdetto è positivo: struttura e componenti sono specifici del progetto, non intercambiabili.

## Sintesi

- Problemi: **P0 0 · P1 7 · P2 7 · P3 4**
- Critici:
  1. Font variabili inesistenti (identità tipografica persa + 2 richieste 404 su ogni pagina)
  2. Indicatore di focus assente sulla ricerca della home e su tutto il footer
  3. Menu mobile (hamburger) e dropdown "Archivio" non operabili correttamente da tastiera o screen reader
  4. Iframe di Internet Archive senza `title` su tutte le 97 schede documento
  5. Suggerimenti della ricerca hero irraggiungibili con Tab e non annunciati

## Problemi per severità

### P1 — Major

**[P1] Font variabili referenziati ma assenti**
- Dove: `assets/stylesheets/fonts.css` righe 22-44; `overrides/main.html` (due `<link rel="preload" as="font">`)
- Categoria: Integrità / Performance
- Impatto: identità tipografica persa su tutto il sito; due 404 e due preload sprecati per ogni pagina vista.
- Raccomandazione: o si aggiungono davvero i due file variabili in `assets/fonts/`, o si riscrive `fonts.css` con una `@font-face` per ciascun file statico esistente (Fraunces 400/600/900, Archivo 500/600/700) e si aggiornano i preload. Attenzione: `--fw-heading: 750` funziona solo con il variabile; con gli statici serve 600 o 900.
- Comando: `/impeccable typeset`

**[P1] Focus non visibile: ricerca hero e footer**
- Dove: `extra.css:388` (`.banner-search input { outline: none }`, senza `:focus-within` sul contenitore); `extra.css:1499-1505` (`.md-footer * { outline: none !important }`)
- Categoria: Accessibilità · WCAG 2.4.7 (AA)
- Impatto: chi naviga da tastiera perde la posizione proprio sul campo principale della home e su tutti i link del footer (verificato: `outlineStyle: none` al focus).
- Raccomandazione: aggiungere `.banner-search:focus-within { … }` con anello ben visibile su fondo fotografico; togliere `outline` dal reset del footer (bastano `box-shadow` e `border`).
- Comando: `/impeccable harden`

**[P1] Hamburger: `<label>` con aria-label, non operabile da tastiera**
- Dove: `overrides/partials/header.html:8`
- Categoria: Accessibilità · WCAG 4.1.2, 2.1.1 · axe `aria-prohibited-attr` (serious) su tutte le pagine mobile
- Impatto: il drawer si apre solo con un clic sulla label del checkbox nascosto; non è un pulsante, non riceve focus. Riguarda anche gli utenti desktop con zoom al 200% (layout mobile).
- Raccomandazione: un `<button type="button" aria-controls="custom-drawer" aria-expanded>` che commuta il checkbox via JS, con gestione di Esc e ritorno del focus.
- Comando: `/impeccable harden`

**[P1] Dropdown "Archivio": stato ARIA statico**
- Dove: `header.html:31-36`; nessun JS aggiorna `aria-expanded`
- Categoria: Accessibilità · WCAG 4.1.2
- Impatto: lo screen reader annuncia sempre "compresso"; il menu si apre per `:focus-within` e non si chiude con Esc; su touch l'apertura dipende dal focus di uno `<span>`.
- Raccomandazione: `<button>` vero con `aria-expanded` sincronizzato, chiusura con Esc e clic esterno.
- Comando: `/impeccable harden`

**[P1] Iframe di Internet Archive senza titolo**
- Dove: `scripts/core/schede.py:467`
- Categoria: Accessibilità · WCAG 4.1.2 · axe `frame-title` (serious)
- Impatto: su ogni scheda il visore del documento è annunciato come "frame" anonimo.
- Raccomandazione: `title="Visore Internet Archive: {titolo}"` e `loading="lazy"`.
- Comando: `/impeccable harden`

**[P1] Link nel testo distinguibili solo per colore**
- Dove: pagina "Il progetto" (link a /documenti/ e simili)
- Categoria: Accessibilità · WCAG 1.4.1 · axe `link-in-text-block` (serious)
- Impatto: rosso su testo scuro ha contrasto 2,47:1 rispetto al testo circostante; senza sottolineatura il link non si riconosce per chi ha deficit cromatici.
- Raccomandazione: sottolineatura sui link in prosa (`.md-typeset p a`), con `text-underline-offset`.
- Comando: `/impeccable typeset`

**[P1] Suggerimenti della ricerca hero: inaccessibili da tastiera e screen reader**
- Dove: `assets/javascripts/hero-search.js` (box spostato in fondo al `<body>`, nessun ruolo ARIA)
- Categoria: Accessibilità · WCAG 4.1.2, 4.1.3, 2.4.3
- Impatto: dopo la digitazione, Tab va al pulsante "Cerca" e poi al resto della pagina; i risultati sono in coda al documento. Nessun annuncio del numero di risultati. In più Invio porta al **primo suggerimento** invece che all'elenco completo, e chi cerca un termine generico finisce su una scheda singola.
- Raccomandazione: pattern combobox (`role="combobox"`, `aria-controls`, `aria-activedescendant`, frecce su/giù, Esc), regione `aria-live` per il conteggio; Invio = ricerca completa, salvo che un suggerimento sia selezionato con le frecce.
- Comando: `/impeccable harden`

### P2 — Minor

**[P2] Target touch sotto soglia**
- Dove (misurati a 390px): "Cita questo documento" / "Schermo intero" 18px di altezza; campo e pulsante ricerca hero 20px; email footer 15px; paginazione 30×26; lettere dell'alfabeto 32×26; chip anni galleria 56×28; chiusura avviso IA 35×24
- Categoria: Responsive · WCAG 2.5.8 (min. 24px) per i primi tre casi; gli altri sono sotto i 44px raccomandati
- Comando: `/impeccable adapt`

**[P2] Immagini senza `width`/`height` e sovradimensionate**
- Dove: tutte le `<img>` generate (0 su 10 in home con dimensioni); `argomenti/fondamenti-del-maoismo.webp` 4524×2206 (568 KB); `profili/dinucci.webp` 1296×1296 (696 KB) usata come avatar; `banner.webp` 1920px servito anche a 390px, senza `srcset`
- Categoria: Performance (CLS/LCP)
- Comando: `/impeccable optimize`

**[P2] Card "Documenti in evidenza" che collassano senza copertina**
- Dove: home mobile, quando la copertina da archive.org non arriva
- Impatto: la card si restringe a circa 70px e il titolo va a capo lettera per lettera ("Imm / agine / non…"). È proprio lo scenario che l'avviso "Internet Archive instabile" prevede.
- Raccomandazione: larghezza fissa della card e `aspect-ratio` sul contenitore immagine, indipendenti dall'immagine.
- Comando: `/impeccable harden`

**[P2] H1 della home nascosto**
- Dove: `<h1>Home</h1>` con `display:none` · axe `page-has-heading-one`
- Raccomandazione: rendere h1 lo slogan della hero ("Documenti, periodici, opuscoli e fonti…"), oggi un `<p>`.
- Comando: `/impeccable clarify`

**[P2] Doppio landmark `<main>`**
- Dove: `/documenti/` (`.risultati-main`) e `/galleria/` (`.galleria-content`) dentro il `<main>` di Material
- Raccomandazione: sostituirli con `<section>` o `<div>`.
- Comando: `/impeccable harden`

**[P2] Overflow orizzontale di 4px su desktop (home)**
- Dove: `extra.css:301` (`.banner-full { width: 100vw }` include la scrollbar)
- Raccomandazione: `width: 100%` con margini negativi calcolati, oppure `100dvw` solo dove la scrollbar è assente.
- Comando: `/impeccable layout`

**[P2] Archivio su mobile: i risultati partono sotto la piega**
- Dove: `/documenti/` a 390px; il pannello filtri occupa tutto il primo schermo
- Raccomandazione: filtri richiudibili in un unico pulsante "Filtri (n)" su mobile.
- Comando: `/impeccable adapt`

### P3 — Rifinitura

- **Emoji usate come icone** (📑 ⛶ 🔗 ⚠️ 🔍 ↺ ✕) in schede, filtri e avvisi: rendering diverso per sistema operativo, peso visivo incoerente con le icone SVG di Material. → `/impeccable polish`
- **Bordo laterale da 4px** (detector `side-tab`) in `documenti.css:132`, `soggetti.css:49`, `soggetti.css:102`: lo stesso accento ripetuto su tre componenti. → `/impeccable polish`
- **Alt ridondanti** nelle card in evidenza (alt = titolo già presente sotto): meglio `alt=""` sulla copertina. Alt del banner ("Archivio del Maoismo Italiano") che non descrive l'immagine. → `/impeccable clarify`
- **Pagina 404 interamente in stili inline** con hex ripetuti (#b71c1c, #6b6b6b, #e3e3e3): fuori dal sistema di token. → `/impeccable polish`

**Falsi positivi esclusi**: il detector segnala Fraunces come "font abusato". Qui è una scelta d'identità coerente (serif editoriale per un archivio) e non va cambiata; il problema reale è che non viene caricata.

## Problemi sistemici

- **Colori fuori dai token**: circa 110 hex/rgba sparsi (extra.css 48, galleria.css 36, home.css 18), con un secondo set parallelo in galleria (`--gal-accent: #b71c1c` duplica `--md-primary-fg-color`).
- **Focus gestito caso per caso**: la galleria ha anelli `:focus-visible` curati, mentre header, hero e footer li tolgono o li lasciano al default del browser (anello scuro di 1px su fondo rosso).
- **Componenti di navigazione senza semantica nativa**: hamburger, dropdown e suggerimenti di ricerca sono costruiti con `label`, `span` e `div` invece di `button` e pattern ARIA.

## Cosa funziona bene

- `hero-search.js`: escaping rigoroso di tutto l'HTML proveniente dai dati, cache del testo ripulito, JSON caricati solo al primo focus.
- Scroll e resize con listener `passive` e `requestAnimationFrame` (galleria), resize con debounce.
- `prefers-reduced-motion` rispettato in header, skeleton, galleria e scroll della timeline.
- Campi di input a 16px per evitare lo zoom di iOS, scelta documentata nel codice.
- Lightbox con gestione da tastiera, `aria-current` sulla timeline, `aria-live` sul pulsante copia, `aria-label` sulla paginazione.
- axe non rileva nessun errore di contrasto del testo (escluso il caso dei link); su mobile non c'è overflow orizzontale in nessuna delle 12 pagine.
- Metadati Open Graph e JSON-LD (BreadcrumbList, CreativeWork, Person, Organization) ben costruiti.

## Azioni consigliate

1. **[P1] `/impeccable typeset`**: riallineare `fonts.css` e i preload ai file statici reali (o aggiungere i variabili); sottolineare i link nella prosa.
2. **[P1] `/impeccable harden`**: hamburger e dropdown come `<button>` con `aria-expanded` ed Esc; focus visibile su hero e footer; `title` all'iframe; combobox accessibile per la ricerca hero e Invio verso la ricerca completa; card in evidenza robuste senza copertina; un solo `<main>`.
3. **[P2] `/impeccable optimize`**: `width`/`height` su tutte le immagini, ridimensionamento di copertine argomenti e avatar, `srcset` per il banner.
4. **[P2] `/impeccable adapt`**: target touch ≥ 24px (meglio 44px), filtri dell'archivio compatti su mobile.
5. **[P2] `/impeccable layout`**: eliminare l'overflow da `100vw` nella hero.
6. **[P2] `/impeccable clarify`**: h1 reale in home, alt delle copertine.
7. **[P3] `/impeccable polish`**: icone SVG al posto delle emoji, colori ricondotti ai token, 404 nel sistema.
