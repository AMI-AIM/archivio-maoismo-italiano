---
name: AMI – Archivio del Maoismo Italiano
description: Archivio digitale di fonti primarie sul maoismo e il marxismo-leninismo italiano, tra catalogo scientifico e stampa militante.
colors:
  rosso-catalogo: "#b71c1c"
  rosso-inchiostro: "#8e0000"
  rosso-tenue: "#f9ecec"
  inchiostro: "#1a1a1a"
  testo: "rgba(0, 0, 0, 0.87)"
  testo-secondario: "#5c5c5c"
  filetto: "rgba(0, 0, 0, 0.07)"
  carta: "#f5f5f5"
  bianco: "#ffffff"
  notte: "#0d0d0d"
  notte-superficie: "#1c1c1c"
  errore: "#d32f2f"
typography:
  display:
    fontFamily: "Fraunces, Georgia, 'Times New Roman', serif"
    fontSize: "clamp(1.45rem, 1.05rem + 1.5vw, 1.9rem)"
    fontWeight: 900
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Fraunces, Georgia, 'Times New Roman', serif"
    fontSize: "1.3rem"
    fontWeight: 750
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Fraunces, Georgia, 'Times New Roman', serif"
    fontSize: "0.9rem"
    fontWeight: 600
    lineHeight: 1.35
  body:
    fontFamily: "Fraunces, Georgia, 'Times New Roman', serif"
    fontSize: "0.8rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Archivo, Arial, 'Helvetica Neue', sans-serif"
    fontSize: "0.65rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.06em"
  data:
    fontFamily: "'Courier Prime', 'Courier New', monospace"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.35
    letterSpacing: "0.02em"
rounded:
  filetto: "0"
  sm: "4px"
  md: "8px"
  card: "12px"
  pillola: "999px"
components:
  button-primary:
    backgroundColor: "{colors.rosso-catalogo}"
    textColor: "{colors.bianco}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "0.6rem 1.5rem"
  button-primary-hover:
    backgroundColor: "{colors.rosso-inchiostro}"
    textColor: "{colors.bianco}"
  etichetta:
    textColor: "{colors.testo-secondario}"
    typography: "{typography.label}"
  segnatura:
    textColor: "{colors.testo-secondario}"
    typography: "{typography.data}"
  chip-filtro:
    backgroundColor: "{colors.carta}"
    textColor: "{colors.rosso-catalogo}"
    rounded: "{rounded.pillola}"
    padding: "0.25rem 0.5rem 0.25rem 0.8rem"
  card-vetrina:
    backgroundColor: "{colors.carta}"
    rounded: "{rounded.card}"
  campo-ricerca:
    backgroundColor: "{colors.bianco}"
    textColor: "{colors.testo}"
    rounded: "{rounded.sm}"
    padding: "0.45rem 0.6rem"
---

# Design System: AMI – Archivio del Maoismo Italiano

## Overview

**Creative North Star: "Catalogo e manifesto"**

Il sito parla con due voci dichiarate. Dove si consulta (archivio, schede documento, liste di persone, organizzazioni e percorsi) vale la sobrietà del catalogo: righe su filetti sottili, segnature dattiloscritte, etichette grigie in maiuscoletto, nessun riquadro superfluo. Dove si entra e si sceglie (home, indici, percorsi tematici) vale l'impatto della stampa militante: fotografie d'epoca a piena larghezza, card con immagine, il rosso pieno delle testate. "Il progetto" è in registro misto: apertura da manifesto, corpo da catalogo.

Il tono è rigoroso ma militante. Il rigore viene dal metodo archivistico: ogni dato ha un posto fisso, una gerarchia leggibile e un carattere che ne dichiara la natura (il testo in Fraunces, le azioni in Archivo, i dati in Courier Prime). La militanza viene dai materiali stessi: il rosso, le testate, le immagini di cortei e opuscoli. Il design non aggiunge retorica propria; lascia parlare le fonti e le incornicia con precisione.

La densità è quella di una sala di consultazione: tanta informazione per schermo, ma ordinata in colonne, con la data sempre in testa alla riga e il titolo come elemento più forte.

**Key Characteristics:**
- Due registri: catalogo (filetti) per consultare, manifesto (card e immagini) per scegliere.
- Tre famiglie con tre ruoli fissi: Fraunces per leggere, Archivo per agire ed etichettare, Courier Prime per i dati.
- Un solo colore d'accento, il rosso, riservato a link, date e azioni primarie.
- Etichette grigie in maiuscoletto, mai blocchi colorati.
- Il documento è al centro: segnatura, scheda dei metadati, documenti collegati.

## Colors

Un rosso da timbro su fondo carta, con neutri caldi e un nero profondo per le fasce-vetrina.

### Primary
- **Rosso catalogo** (`rosso-catalogo`): header, link, date in testa alle righe, pulsanti primari, voce di filtro selezionata, segnatura AMI nella scheda. È il segno della mano del catalogatore.
- **Rosso inchiostro** (`rosso-inchiostro`): stato di passaggio del mouse e accento di Material. Più scuro del primario per restare leggibile sia come testo sul bianco sia come fondo sotto il testo bianco.
- **Rosso tenue** (`rosso-tenue`): evidenziazioni chiare (voce attiva, sfondi di selezione).

### Neutral
- **Testo** (`testo`): titoli e corpo su fondo chiaro.
- **Testo secondario** (`testo-secondario`): etichette, metadati, date di vita, contatori. Scelto per superare il 4,5:1 anche sul fondo carta.
- **Filetto** (`filetto`): linee di separazione tra righe, bordi dei campi, divisori tra colonne.
- **Carta** (`carta`): fondo delle card-vetrina, dei chip e dei riquadri di nota.
- **Bianco** (`bianco`): fondo della pagina; testo e icone su rosso, nero e fotografie.
- **Inchiostro** (`inchiostro`): testo su superfici chiare sospese (tendine, pannelli).
- **Notte** (`notte`, `notte-superficie`): fascia "Documenti in evidenza" in home e le sue copertine.
- **Errore** (`errore`): messaggi di errore e stati non riusciti.

### Named Rules
**The Red Pencil Rule.** Nel registro catalogo il rosso segna solo ciò che si clicca o che data un documento: link, date, pulsanti primari, selezione. Etichette, badge e categorie non sono mai rossi.

**The Press Accent Rule.** Nel registro manifesto (home) il rosso torna accento di stampa: barrette sotto i titoli di sezione, icone dei titoli, avatar con iniziali "a timbro" (cerchio bianco, bordo e iniziali rossi). Senza questi accenti la home diventa anonima.

**The Darker Hover Rule.** Al passaggio del mouse il rosso si scurisce (rosso inchiostro), non si schiarisce. Un rosso più chiaro perde contrasto sul bianco.

## Typography

**Display Font:** Fraunces (con Georgia, Times New Roman e serif CJK di sistema per i testi in cinese)
**Body Font:** Fraunces (stessa famiglia: la gerarchia cambia il peso, non lo scheletro)
**Label Font:** Archivo (con Arial, Helvetica Neue)
**Data Font:** Courier Prime (con Courier New)

**Character:** un serif editoriale variabile per tutto ciò che si legge, un grottesco sobrio per tutto ciò che si fa, una macchina da scrivere per tutto ciò che è dato d'archivio. La radice del sito è al 125% (1rem = 20px): i valori in rem del frontmatter vanno letti su questa base.

### Hierarchy
- **Display** (900, 29–38px fluido, interlinea 1,2): titolo di pagina (documento, persona, organizzazione, percorso). Sempre color testo, mai rosso.
- **Headline** (750, 26px): titoli di sezione ("Descrizione", "Scheda", "Nell'archivio", "Documenti", "In evidenza").
- **Gruppo** (650, 21px): sottosezioni dentro una sezione ("Come autore", "Pubblicazioni").
- **Title** (600, 18px, interlinea 1,35): titolo di riga negli elenchi e nei risultati.
- **Body** (400, 16px, interlinea 1,6, misura 68ch): descrizioni, biografie, testo del progetto. La misura delle biografie resta 68ch.
- **Label** (600, 13px, maiuscolo, spaziatura 0,06em): etichette di campo nella Scheda, tipologia, ruolo secondario ("anche menzionato"), categorie delle organizzazioni.
- **Data** (400, 15px): segnatura AMI, valori della Scheda, chiavi di "Nell'archivio", conteggi nei filtri.

### Named Rules
**The Three Voices Rule.** Ogni testo appartiene a una sola voce: Fraunces se si legge, Archivo se si clicca o etichetta, Courier Prime se è un dato di catalogo. Le azioni (link "Tutti i documenti di…", "Cita questo documento", Reset) non vanno mai in Courier. Eccezione dichiarata: nella Scheda i valori restano in Courier anche quando sono link (autore, organizzazione, percorsi tematici), in rosso: sono dati prima che azioni.

**The Weight Ladder Rule.** La gerarchia dei titoli si fa col peso di Fraunces (900 → 750 → 650 → 600), non cambiando famiglia.

**The Date Stays Serif Rule.** Le date in testa alle righe restano in Fraunces rosso, in tutte le liste del sito; il Courier è per la segnatura e i valori di metadato.

## Layout

Contenitore centrato di Material (circa 1220px utili su desktop), margine laterale di 16px su telefono.

- **Archivio:** colonna filtri di 300px separata dai risultati da un filetto verticale, fissa allo scorrimento su desktop; sopra i 768px i filtri sono sempre aperti, sotto si chiudono dietro "Mostra filtri" e la ricerca testuale resta visibile in cima.
- **Scheda documento:** percorso di navigazione, segnatura, titolo, visore a tutta larghezza, poi Descrizione e Scheda affiancate (colonna Scheda tra 16 e 20rem); sotto i 900px si impilano.
- **Righe di catalogo:** data a sinistra, titolo e metadati a destra. In ogni elenco la colonna della data è larga quanto la data più lunga di quell'elenco (subgrid); sotto i 600px (480px in "Nell'archivio") la data va sopra il titolo.
- **Vetrine:** griglie di card a tre colonne (indici) o a una colonna di banner (percorsi tematici); a due colonne sotto i 900px e a una sotto i 600px.
- **Soglie usate:** 480px, 600px, 768px, 900px, 1100px; schermi touch (pointer: coarse) con aree cliccabili di almeno 44px.

### Named Rules
**The Hairline Rule.** Nel registro catalogo le righe si separano con un filetto di 1px, non con riquadri o sfondi alternati.

## Elevation & Depth

Sistema ibrido, diviso per registro. Le pagine di consultazione sono piatte: nessuna ombra, profondità data solo da filetti e spaziatura. Le pagine-vetrina usano ombre morbide e diffuse sulle card, che si sollevano leggermente al passaggio del mouse. Le superfici sospese (tendine del menu, pannelli, pillole dello slider) hanno un'ombra breve per staccarsi dal contenuto.

### Shadow Vocabulary
- **Sollevamento card** (`box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08)` con `translateY(-4px)`): card-vetrina al passaggio del mouse.
- **Superficie sospesa** (`box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12)`): tendine e pannelli.
- **Maniglia** (`box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25)`): maniglie e pillole dello slider anno.

### Named Rules
**The Two Registers Rule.** Le ombre esistono solo nel registro manifesto (home, indici di Persone e Organizzazioni, percorsi tematici). Archivio, schede documento e liste restano piatti. "Il progetto" è in registro misto: apertura da manifesto (lead a 18px, barretta rossa sotto il titolo, segnatura della raccolta), corpo da catalogo (righe su filetti, note su filetto, nessun riquadro né ombra).

## Shapes

Angoli diritti o appena arrotondati nel catalogo, morbidi nelle vetrine.

- **Filetti e righe** (0): elenchi, Scheda, filtri.
- **Campi e pulsanti** (4px): ricerca, select di ordinamento, pulsanti primari, riquadro del visore.
- **Riquadri di nota** (8px): pannelli di ricerca negli indici.
- **Card-vetrina** (12px): card di persone, organizzazioni e percorsi.
- **Pillole** (999px): chip dei filtri attivi, pillole degli anni nello slider.
- **Cerchi**: avatar con iniziali in home "a timbro": fondo bianco, bordo di 2px e iniziali in rosso catalogo.

## Components

### Buttons
Netti, rossi, senza ornamenti.
- **Shape:** angoli appena arrotondati (4px).
- **Primary:** fondo rosso catalogo, testo bianco in Archivo 600, padding 0,6rem × 1,5rem.
- **Hover / Focus:** fondo rosso inchiostro; anello di focus di 2px rosso a 2px di distanza, sempre bianco su fondi rossi, scuri o fotografici (header, testata della home, fascia "in evidenza", footer).
- **Azioni secondarie** (Cita questo documento, Schermo intero, Apri su Internet Archive): testo rosso in Archivo con icona SVG, senza fondo.

### Chips
- **Filtri attivi:** pillola su fondo carta con bordo e testo rossi, nome del gruppo in grassetto ("Organizzazione: …") e pulsante ✕ per rimuoverla.

### Cards / Containers
- **Corner Style:** 12px.
- **Background:** fondo carta, immagine a proporzione fissa (4:3) in alto, testo sotto un filetto. Senza immagine: iniziali a timbro al centro dell'area, mai una sagoma generica.
- **Shadow Strategy:** vedi Elevation & Depth, solo registro manifesto.
- **Border:** filetto di 1px.
- **Internal Padding:** circa 0,6 × 1rem nella parte testuale.

### Inputs / Fields
- **Style:** filetto di 1px, fondo bianco, angoli 4px, testo a 16px (sotto, iOS ingrandisce la pagina).
- **Focus:** bordo e anello rossi.
- **Filtri a spunta:** caselle native colorate di rosso, nome completo che va a capo, conteggio in Courier a destra; la voce selezionata diventa rossa e in grassetto. Sopra le 10 voci compare un campo per restringere l'elenco.

### Navigation
- **Header:** fascia rossa piena, voci in Archivo 600 bianche, voce attiva sottolineata anche nelle pagine interne della sezione (una scheda documento accende "Archivio", una persona accende "Persone"); menu "Archivio" a tendina (Tutti i documenti, Percorsi tematici, Galleria).
- **Avviso Internet Archive:** sempre in cima. Su desktop fisso, su telefono una riga breve che scorre via con la pagina e non copre l'header.
- **Percorso di navigazione:** sopra il titolo, in Archivo grigio con separatore "›" ("Archivio › Opuscolo", "Persone", "Archivio › Percorsi tematici").
- **Mobile:** menu laterale con intestazione rossa e logo; link "Vai al contenuto" come primo elemento raggiungibile da tastiera.

### Segnatura
La firma del sistema. In testa alla scheda documento, prima del titolo: id AMI in rosso, tipologia e data in Courier Prime grigio, separati da punti ("AMI-0043 · Opuscolo · 1968"). Ripresa in piccolo accanto alla data in ogni risultato dell'archivio.

### Scheda dei metadati
Elenco di definizioni su filetti: etichetta in Archivo grigio maiuscoletto, valore in Courier Prime. Mostra solo i campi compilati; i valori "N/A" non compaiono.

### Riga di catalogo
Un solo componente in home, percorsi tematici, persone e organizzazioni: data rossa in Fraunces regolare nella colonna adattiva, titolo in Fraunces 600, poi una riga di metadati (tipologia come etichetta grigia, organizzazione in Archivo grigio, eventuale ruolo secondario). Al passaggio del mouse solo il fondo carta, nessuna striscia colorata. Nelle pagine di persone e organizzazioni le righe sono raggruppate per ruolo, con il conteggio del gruppo.
- **Variante compatta** ("Nell'archivio"): data e titolo, senza metadati.
- **Variante estesa** (risultati dell'archivio): data · segnatura in Courier, titolo, autore · organizzazione · tipologia, estratto della descrizione.

### Pagina "Il progetto"
Registro misto. Corpo a una sola misura (30rem, 600px: circa 75-80 battute) per prosa, titoli, aree, note, Scheda della raccolta, bibliografia e citazione; solo l'apertura è più larga.
- **Apertura:** titolo con barretta rossa (Press Accent Rule). Sopra i 1220px griglia di 46rem: lead in Fraunces 22px e presentazione a sinistra, segnatura della raccolta in colonna a destra (voci su filetti, "AMI" rosso). Sotto, segnatura in riga tra due filetti, con i separatori "·" che non restano mai a inizio riga. Valori dalla Scheda (`scripts/core/raccolta.py`).
- **Aree del patrimonio:** vetrina, non partizione (le opere di Mao sono anche pubblicazioni del PCC): righe-link su filetti senza conteggi, titolo, testo grigio, azione rossa in Archivo.
- **Ordine:** presentazione, aree, Consultazione con il pulsante primario "Esplora l'archivio", poi Norme di descrizione, Bibliografia, Come citare, Contatti.
- **Titoli di sezione:** su filetto, come nelle schede documento.
- **Indice:** quello di Material nella colonna destra sopra i 960px; sotto, "In questa pagina" richiudibile, generato da `raccolta.py` dai titoli ## e ### (voci di 44px).
- **Scheda della raccolta:** `<details>` aperto su desktop (sommario nascosto), chiuso su telefono con "Mostra i N campi".
- **Note e bibliografia:** "Convenzioni" su filetto, senza riquadro; bibliografia a corpo testo con rientro sporgente e cognomi in maiuscolo ridotto (`.autore`).
- **Come citare:** stesso pannello di "Cita questo documento" (Chicago, MLA, BibTeX, Semplice; data del giorno), sempre aperto, senza fondo né riquadri, solo due filetti; "Copia" resta il pulsante rosso pieno delle schede. L'URL va a capo solo dopo le "/".

### Testata di persona e organizzazione
Con testo curatoriale: biografia o storia su fondo carta accanto all'immagine. Senza testo: nessun riquadro, immagine di 180px subito accanto al blocco di nome e date, una riga "in fase di redazione". Senza immagine: solo nome e date, nessun segnaposto (le iniziali "a timbro" servono solo nelle card "In evidenza" degli indici). Sempre il link "Vedi questi documenti nell'archivio" (archivio già filtrato).

## Do's and Don'ts

### Do:
- **Do** separare le righe di consultazione con filetti di 1px (The Hairline Rule).
- **Do** mettere in Courier Prime segnature, valori di metadato e conteggi; in Archivo azioni ed etichette; in Fraunces tutto ciò che si legge (The Three Voices Rule).
- **Do** usare il rosso solo per link, date, selezione e pulsanti primari (The Red Pencil Rule).
- **Do** scurire il rosso al passaggio del mouse (The Darker Hover Rule).
- **Do** mostrare le date incerte come "s.d." (anno ignoto) e "ca. 2010" (cifre finali ignote).
- **Do** mantenere card con immagine e ombre morbide nelle pagine-vetrina: sono una scelta di impatto, non un residuo.
- **Do** garantire aree cliccabili di almeno 44px sugli schermi touch e un anello di focus visibile su ogni controllo.

### Don't:
- **Don't** usare blocchi o badge rossi pieni per etichette, ruoli o categorie: sono grigi, in maiuscoletto, senza fondo.
- **Don't** aggiungere ombre o riquadri nelle pagine di consultazione (The Two Registers Rule).
- **Don't** usare Courier Prime per link e azioni (unica eccezione: i valori della Scheda).
- **Don't** mettere titoli di pagina in rosso, né colorare di rosso titoli di card non cliccabili; nel registro catalogo niente rosso decorativo (in home sì: The Press Accent Rule).
- **Don't** usare emoji come icone: le icone sono SVG con lo stesso tratto.
- **Don't** troncare i nomi nei filtri: vanno a capo interi.
- **Don't** mostrare un titolo visibile in home (resta solo quello per i lettori di schermo) e non rimuovere l'avviso sullo stato di Internet Archive in cima alla pagina.
