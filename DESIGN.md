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
  xs: "2px"
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

Fuori scala, dichiarati come variabili: il lead d'apertura del progetto (`--ami-font-size-lead`, 22px), il "404" monumentale (`--ami-size-404`) e i titoli-manifesto della galleria (`--gal-size-titolo`, `--gal-size-anno`, `--gal-size-anno-telefono`).

**Lingua:** i caratteri cinesi sono marcati `lang="zh-Hans"` in fase di build (hook `scripts/hooks/lingua_cinese.py`), così i lettori di schermo cambiano voce e il browser sceglie glifi cinesi.

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

In CSS i raggi sono le variabili `--ami-radius-xs|sm|md|card|pillola` (extra.css, `:root`): niente valori scritti a mano. Unica eccezione rimasta: le card dei percorsi tematici (argomenti.css), in attesa di decidere il futuro dei percorsi.

- **Filetti e righe** (0): elenchi, Scheda, filtri.
- **Segni** (2px, `xs`): barre dell'istogramma, sottolineature, piccoli riquadri squadrati.
- **Campi e pulsanti** (4px): ricerca, select di ordinamento, pulsanti primari, riquadro del visore.
- **Superfici sospese e riquadri di nota** (8px, `md`): tendine del menu, pannelli, pannelli di ricerca negli indici.
- **Card-vetrina** (12px): card di persone, organizzazioni e percorsi.
- **Pillole** (999px): chip dei filtri attivi, pillole degli anni nello slider, ricerca della home, pulsante "Filtri" flottante su telefono.
- **Cerchi**: avatar con iniziali in home "a timbro": fondo bianco, bordo di 2px e iniziali in rosso catalogo.

## Components

### Buttons
Netti, rossi, senza ornamenti.
- **Shape:** angoli appena arrotondati (4px).
- **Primary:** fondo rosso catalogo, testo bianco in Archivo 600, padding 0,6rem × 1,5rem.
- **Hover / Focus:** fondo rosso inchiostro; anello di focus di 2px rosso a 2px di distanza, sempre bianco su fondi rossi, scuri o fotografici (header, testata della home, fascia "in evidenza", footer).
- **Azioni secondarie** (Cita questo documento, Schermo intero, Apri su Internet Archive, Azzera filtri nel pannello dell'archivio): testo rosso in Archivo, con icona SVG dove serve, senza fondo. «Azzera filtri» diventa pulsante pieno solo nello stato vuoto dei risultati, dove è l'unica via d'uscita.

### Chips
- **Filtri attivi:** pillola su fondo carta con bordo e testo rossi, nome del gruppo in grassetto ("Organizzazione: …") e pulsante ✕ per rimuoverla, che ai lettori di schermo dice quale filtro toglie («Rimuovi il filtro Persona: Mao Zedong»).

### Cards / Containers
- **Corner Style:** 12px.
- **Background:** fondo carta, immagine a proporzione fissa (4:3) in alto, testo sotto un filetto. Senza immagine: iniziali a timbro al centro dell'area, mai una sagoma generica.
- **Shadow Strategy:** vedi Elevation & Depth, solo registro manifesto.
- **Border:** filetto di 1px.
- **Internal Padding:** circa 0,6 × 1rem nella parte testuale.
- **Card degli indici Persone/Organizzazioni:** categoria in maiuscoletto (solo organizzazioni), nome in Fraunces 650 che diventa rosso al passaggio del mouse, poi una sola riga «date · N documenti»: date in Fraunces corsivo, conteggio in Courier. Gli intervalli aperti restano nella forma archivistica «1921 –» (scelta del curatore: più rigorosa di «dal 1921»). Il timbro delle iniziali in «In evidenza» è di 110px (84px su telefono), non domina la card. L'elenco «Tutte le persone» e la barra A–Z seguono il **cognome** (colonna Cognome di dati.xlsx: Brandirali sotto la B, Del Carria sotto la D), mentre il nome resta scritto nella forma naturale; i pulsanti delle lettere dichiarano la selezione con `aria-pressed`.

### Inputs / Fields
- **Style:** filetto di 1px, fondo bianco, angoli 4px, testo a 16px (sotto, iOS ingrandisce la pagina).
- **Focus:** bordo e anello rossi.
- **Filtri a spunta:** caselle native colorate di rosso, nome completo che va a capo, conteggio in Courier a destra; la voce selezionata diventa rossa e in grassetto. Sopra le 10 voci compare un campo per restringere l'elenco, che trova le voci di Persona e Organizzazione anche con le "Altre forme del nome" (es. "Lin Piao" → Lin Biao) senza mostrarle. Le persone sono in ordine di cognome, come nell'indice. I conteggi seguono i risultati: ogni numero dice quanti documenti darebbe quella voce con gli altri filtri attivi; le voci a 0 si attenuano in grigio (testo secondario) ma restano al loro posto e cliccabili.
- **Ricerca testuale dell'archivio:** ogni parola deve comparire come inizio di parola (accenti ignorati); cerca anche segnatura e nomi collegati. Una parola sola resta intera ("lenin" non trova "marxista-leninista"), ma tra parole vicine trattino e spazio si equivalgono: "mao tse tung" trova "Mao Tse-tung", "ciu en lai" trova "Ciu-En-lai". Le grafie varianti NON entrano nei risultati; se però la query contiene un'altra forma del nome, sopra i risultati compare una riga su filetto, «Nel catalogo: **Mao Zedong** (anche «Mao Tse-tung»)», con l'azione rossa «Vedi i N documenti collegati» che applica il filtro Persona (o Organizzazione) e toglie il testo. Se la ricerca dà zero risultati la riga non compare: lo stato vuoto dice «Nessun documento contiene «Ciu En-lai» nel testo. Nel catalogo il nome è Zhou Enlai.» e il pulsante pieno diventa «Vedi i 2 documenti di Zhou Enlai», con «Azzera filtri» sotto come azione secondaria.
- **Paginazione:** ogni cambio di pagina è una voce di cronologia (Indietro torna alla pagina precedente dei risultati); la vista torna in cima ai risultati e il focus va sul conteggio.
- **Pulsante "Filtri" flottante:** solo su telefono, compare quando il pannello filtri esce dallo schermo; riapre il pannello.

### Navigation
- **Header:** fascia rossa piena, voci in Archivo 600 bianche, voce attiva sottolineata anche nelle pagine interne della sezione (una scheda documento accende "Archivio", una persona accende "Persone"); menu "Archivio" a tendina (Tutti i documenti, Percorsi tematici, Galleria).
- **Avviso Internet Archive:** sempre in cima. Su desktop fisso, su telefono una riga breve che scorre via con la pagina e non copre l'header.
- **Percorso di navigazione:** sopra il titolo, in Archivo grigio con separatore "›" ("Archivio › Opuscolo", "Persone", "Archivio › Percorsi tematici"). Nelle schede aperte dall'archivio con filtri o pagina, in fondo alla riga compare l'azione rossa «Torna ai risultati» (icona SVG a chevron), che riporta all'ultima ricerca; "Archivio" porta sempre all'archivio intero. Tornando così, la lista si apre alla riga della scheda appena letta, con il focus sul titolo e un fondo rosso tenue che si spegne in circa due secondi (fisso con il movimento ridotto).
- **Mobile:** menu laterale con intestazione rossa e logo; link "Vai al contenuto" come primo elemento raggiungibile da tastiera.

### Segnatura
La firma del sistema. In testa alla scheda documento, prima del titolo: id AMI in rosso, tipologia e data in Courier Prime grigio, separati da punti ("AMI-0043 · Opuscolo · 1968"). Ripresa in piccolo accanto alla data in ogni risultato dell'archivio.

### Scheda dei metadati
Elenco di definizioni su filetti: etichetta in Archivo grigio maiuscoletto, valore in Courier Prime. Mostra solo i campi compilati; i valori "N/A" non compaiono.

### Riga di catalogo
Un solo componente in home, percorsi tematici, persone e organizzazioni: data rossa in Fraunces regolare nella colonna adattiva, titolo in Fraunces 600, poi una riga di metadati (tipologia come etichetta grigia, organizzazione in Archivo grigio, eventuale ruolo secondario, preceduto da «·»: «Opuscolo · anche come autore»). Al passaggio del mouse solo il fondo carta, nessuna striscia colorata. Nelle pagine di persone e organizzazioni le righe sono raggruppate per ruolo, con il conteggio del gruppo.
- **Variante compatta** ("Nell'archivio"): data e titolo, senza metadati.
- **Variante estesa** (risultati dell'archivio): data · segnatura in Courier, titolo, autore · organizzazione · tipologia, estratto della descrizione.

### Pagina "Il progetto"
Registro misto. Corpo a una sola misura (30rem, 600px: circa 75-80 battute) per prosa, titoli, aree, note, Scheda della raccolta, bibliografia e citazione; solo l'apertura è più larga.
- **Apertura:** titolo con barretta rossa (Press Accent Rule) e una fotografia dell'archivio stesso, mai un'immagine decorativa: AMI-0062 (studenti di Trieste sulla nave cinese Jinsha, 1968), dalla miniatura locale, con didascalia in Fraunces grigio e segnatura in Courier rossa che porta alla scheda. Sopra i 1220px griglia di 46rem: a sinistra lead in Fraunces 22px, presentazione e segnatura della raccolta in riga tra due filetti; a destra la fotografia intera (15rem). Sotto i 1220px la fotografia segue il lead, ritagliata in 5:4 dall'alto. I separatori "·" della segnatura non restano mai a inizio riga. Valori dalla Scheda (`scripts/core/raccolta.py`), più il rimando "Scheda completa ›" alla sezione "La raccolta".
- **Il patrimonio:** vetrina, non partizione (le opere di Mao sono anche pubblicazioni del PCC), introdotta da "L'AMI raccoglie, tra l'altro:": righe-link su filetti senza conteggi, titolo, testo grigio, azione rossa in Archivo in una colonna fissa di 10rem allineata a destra (sotto il testo su telefono).
- **Ordine:** presentazione, Il patrimonio, Consultazione con il pulsante primario "Esplora l'archivio", La raccolta (Scheda ISAD), Norme di descrizione, Bibliografia (cinque gruppi tematici con sottotitoli h3 in HTML, fuori dall'indice), Come citare, Contatti.
- **Titoli di sezione:** su filetto, come nelle schede documento.
- **Indice:** quello di Material nella colonna destra sopra i 960px; sotto, "In questa pagina" richiudibile, generato da `raccolta.py` dai titoli ## e ### (voci di 44px).
- **Scheda della raccolta:** sezione propria ("La raccolta"); `<details>` aperto su desktop (sommario nascosto), chiuso su telefono con "Mostra i N campi" e "Nascondi i campi" anche in fondo.
- **Note e bibliografia:** "Convenzioni" su filetto, senza riquadro; bibliografia a corpo testo con rientro sporgente e cognomi in maiuscolo ridotto (`.autore`).
- **Come citare:** stesso pannello di "Cita questo documento" (Chicago, MLA, BibTeX, Semplice; data del giorno), sempre aperto, con il fondo carta e il riquadro bianco delle schede (unico riquadro del corpo, voluto); "Copia" resta il pulsante rosso pieno. L'URL va a capo solo dopo le "/".

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
- **Don't** mostrare un titolo visibile in home (resta solo quello per i lettori di schermo).
- **Don't** mostrare l'avviso su Internet Archive dove non serve: il banner (non adesivo, dopo «Vai al contenuto») compare solo in galleria; nelle schede documento l'avviso sta dentro il visore, che si richiude a una fascia con miniatura locale e «Riprova». Il banner è in nero inchiostro con filetto e icona rossi (non più marrone/ambra). Banner e avviso nel visore usano la stessa frase: «I documenti di questo archivio sono ospitati su Internet Archive, piattaforma al momento instabile o irraggiungibile…».
- **Don't** introdurre un tema scuro senza progettarlo: oggi il sito ha un solo schema chiaro (i colori "notte" servono solo alla fascia in evidenza della home).
