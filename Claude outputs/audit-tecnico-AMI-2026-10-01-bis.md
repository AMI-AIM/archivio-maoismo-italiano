# Audit tecnico (secondo passaggio) — Archivio del Maoismo Italiano

Data: 1 ottobre 2026 · Confronto con l'audit del mattino (11/20).
Oggetto: sorgenti nella cartella GitHub locale dopo `typeset`, la correzione delle descrizioni, `harden` e il titolo di sezione del drawer.
Metodo: stesso protocollo del primo audit (axe-core 4, WCAG 2.0/2.1 A-AA + best practice; Chromium/Playwright su 12 pagine a 1440×900 e 390×844; detector Impeccable).
Limite importante: il sito non è stato rigenerato con il Launcher (richiede la cache di Internet Archive che sta sul tuo computer). Il rebuild è stato **emulato** sull'ultima versione pubblicata: header renderizzato dal nuovo template, CSS/JS aggiornati, markup dei generatori patchato come nei `.py`. archive.org era irraggiungibile dall'ambiente di test.

## Punteggio

| # | Dimensione | Prima | Ora | Problema principale rimasto |
|---|---|---|---|---|
| 1 | Accessibilità | 2 | **3** | Home senza `<h1>`; azioni della scheda (Cita, Schermo intero) alte 17-18px |
| 2 | Performance | 2 | **2** | Immagini senza `width`/`height`, copertine e avatar sovradimensionati |
| 3 | Responsive | 3 | **3** | Target touch piccoli; 4px di overflow orizzontale in home (desktop) |
| 4 | Theming | 2 | **2** | ~110 colori hard-coded, token paralleli in galleria |
| 5 | Integrità implementativa | 2 | **3** | Emoji come icone nelle schede; bordi laterali da 4px |
| **Totale** | | **11/20** | **13/20** | **Accettabile, vicino a "Buono"** |

## Verdetto sull'integrità implementativa: SUPERATO

Il sistema tipografico dichiarato ora arriva al browser: `document.fonts` riporta Fraunces e Archivo caricati su tutte le 24 combinazioni pagina/viewport, zero richieste 404 sui font (prima 2 per pagina). Navigazione, menu e ricerca usano elementi nativi (`<button>`, `<nav>`) con stato ARIA sincronizzato. Restano incoerenze minori (emoji, bordi laterali), non sistemiche.

## Cosa è cambiato (verificato)

- **axe**: da 7 tipi di violazione (3 "serious") a **2 residui**, entrambi in home: `page-has-heading-one` (moderate) e `image-redundant-alt` (minor). Nessuna violazione su 22 delle 24 combinazioni.
- **Risolti**: font 404; link nella prosa senza sottolineatura; focus invisibile su ricerca hero e footer; hamburger non operabile; dropdown con `aria-expanded` statico; iframe senza titolo; suggerimenti della ricerca irraggiungibili e Invio che apriva il primo suggerimento; doppio `<main>`; `h4` saltato nei filtri; card in evidenza che collassavano senza copertina; avviso Internet Archive che copriva il menu mobile.
- **Prove da tastiera** (Chromium): dropdown aperto/chiuso con Invio, frecce ed Esc con ritorno del focus; drawer con trappola del focus, Esc, pulsante Chiudi, tap sull'overlay; ricerca hero con frecce, Esc, Invio verso `documenti/?q=…`, stato di errore con dati non caricabili; catalogo dell'Archivio con errore 503 simulato e pulsante Riprova funzionante.
- **Non verificato**: dispositivi touch reali, lettori di schermo reali (VoiceOver/NVDA), build MkDocs vera.

## Problemi aperti

**P0: 0 · P1: 0 · P2: 5 · P3: 4**

### P2

- **[P2] Home senza titolo principale.** `<h1>Home</h1>` nascosto; lo slogan della hero è un `<p>`. Impatto: lettori di schermo e motori di ricerca non trovano il titolo della pagina più importante. → `/impeccable clarify`
- **[P2] Target sotto i 24px (WCAG 2.5.8).** Scheda: "Cita questo documento" 18px, "Schermo intero" 17px; ricerca hero: campo 20px (la "pillola" intorno non è cliccabile), "Cerca" 19px; link del footer 18-21px con 0,3rem di spazio tra loro. Paginazione (30×26) e lettere dell'alfabeto (32×26) superano i 24px ma restano sotto i 44 consigliati. → `/impeccable adapt`
- **[P2] Immagini senza dimensioni e troppo pesanti.** 0 immagini su 98 controllate hanno `width`/`height` (spostamenti di layout al caricamento); `fondamenti-del-maoismo.webp` 4524px / 568 KB, `dinucci.webp` 1296² / 696 KB usata come avatar; banner 1920px servito anche al telefono, senza `srcset`. → `/impeccable optimize`
- **[P2] Overflow orizzontale di 4px** in home su desktop (`.banner-full { width: 100vw }`). → `/impeccable layout`
- **[P2] Archivio su mobile**: il pannello filtri occupa tutto il primo schermo, i risultati partono sotto la piega. → `/impeccable adapt`

### P3

- Emoji come icone nelle schede e negli elenchi (📑 ⛶ 🔗 📋 🔍): l'avviso Internet Archive ora usa SVG, il resto no. → `/impeccable polish`
- Bordi laterali da 4px su abstract e biografie (`documenti.css:132`, `soggetti.css:49`, `soggetti.css:102`). → `/impeccable polish`
- Stato "Immagine non disponibile" (riquadri rosa su fascia nera): ora non collassa, ma stride sul fondo scuro della home. → `/impeccable polish`
- Pagina 404 in stili inline con colori hard-coded; alt delle copertine in evidenza ridondanti col titolo sotto. → `/impeccable polish`, `/impeccable clarify`

## Problemi sistemici

- **Colori fuori dai token**: invariati nella sostanza (extra.css 54, galleria.css 36, home.css 18 valori hex). Il blocco aggiunto con `harden` usa il bianco per gli anelli di focus su fondi scuri: scelta voluta, ma andrebbe resa un token (`--ami-focus-on-dark`).
- **Immagini gestite a mano**: dimensioni, pesi e `srcset` non sono generati dagli script Python, quindi ogni nuova immagine riapre il problema. La soluzione duratura è nei generatori, non nel CSS.

## Cosa funziona bene

- Tipografia finalmente coerente su tutto il sito, con i pesi previsti dalla scala (h1 900, h2 750, h3 650).
- Navigazione accessibile da tastiera end-to-end, con stati annunciati.
- Stati di errore con una via d'uscita (Riprova, ricerca completa) invece del silenzio.
- Nessun overflow su mobile in 12 pagine; nessun errore JavaScript in pagina.

## Azioni consigliate

1. **[P2] `/impeccable adapt`**: target ≥ 24px (meglio 44) su azioni della scheda, ricerca hero, footer, paginazione e alfabeto; filtri compatti su mobile.
2. **[P2] `/impeccable optimize`**: `width`/`height` generati dagli script, ridimensionamento delle immagini pesanti, `srcset` per il banner.
3. **[P2] `/impeccable clarify`**: `<h1>` reale in home; alt delle copertine.
4. **[P2] `/impeccable layout`**: overflow da `100vw` nella hero.
5. **[P3] `/impeccable polish`**: icone SVG al posto delle emoji, stato "immagine non disponibile" sul fondo scuro, 404 nel sistema di token.
