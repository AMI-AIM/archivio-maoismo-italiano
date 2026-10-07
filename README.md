# AMI — Archivio del Maoismo Italiano



## Descrizione

**AMI — Archivio del Maoismo Italiano** è un progetto digitale dedicato alla raccolta, descrizione e valorizzazione delle fonti storiche relative al maoismo in Italia.

L'obiettivo dell'archivio è rendere accessibile un patrimonio documentario spesso disperso: opuscoli, periodici, libri, manifesti, documenti politici e materiali prodotti da organizzazioni, gruppi e militanti della galassia maoista italiana tra gli anni Sessanta e Settanta del Novecento.

Il progetto nasce con l'intento di fornire uno strumento utile alla ricerca storica, mettendo in relazione documenti, persone, organizzazioni e contesti politici.

## Obiettivi

AMI si propone di:

* preservare la memoria documentaria del maoismo italiano;
* facilitare l'accesso a fonti primarie difficilmente reperibili;
* costruire un repertorio digitale interrogabile;
* favorire la ricerca sulla storia del comunismo italiano, della nuova sinistra e dei movimenti rivoluzionari del secondo Novecento;
* documentare la circolazione delle idee maoiste nel contesto politico e culturale italiano.

## Struttura dell'archivio

L'archivio è organizzato attraverso diverse tipologie di dati:

### Documenti

La sezione principale raccoglie le fonti digitalizzate, con informazioni descrittive quali:

* titolo;
* autore o ente produttore;
* anno di pubblicazione;
* tipologia del documento;
* organizzazione di riferimento;
* parole chiave tematiche;
* collegamento alla risorsa digitale.

### Persone

Una sezione dedicata ai protagonisti collegati ai documenti:

* militanti;
* dirigenti politici;
* autori;
* figure storiche del movimento comunista internazionale.

### Organizzazioni

Una sezione dedicata ai gruppi politici e alle organizzazioni che hanno prodotto o diffuso materiali maoisti in Italia.

Questa struttura permette di ricostruire reti politiche e culturali oltre la semplice catalogazione bibliografica.

## Ambito storico

L'archivio riguarda principalmente:

* il maoismo italiano;
* il marxismo-leninismo degli anni Sessanta e Settanta;
* la nuova sinistra italiana;
* la propaganda e l'editoria politica militante;
* i rapporti tra Italia, Cina e movimento comunista internazionale durante la Guerra fredda.

## Fonti

I materiali sono organizzati attraverso schede archivistiche e collegati alle relative copie digitali disponibili online.

Le fonti comprendono principalmente:

* pubblicazioni teoriche;
* opuscoli politici;
* riviste militanti;
* documenti congressuali;
* materiali prodotti da organizzazioni comuniste.

## Tecnologia

Il sito è sviluppato come archivio digitale statico.

Tecnologie principali:

* **GitHub Pages** per la pubblicazione;
* **Markdown** per la gestione dei contenuti;
* strumenti di versionamento Git;
* metadati strutturati per la descrizione dei documenti.

La pipeline di generazione (Excel → Markdown → MkDocs Material) è interamente
in Python: i dati sorgente stanno in `data/dati.xlsx`, gli script in `scripts/`
(punto d'ingresso: `python Launcher.py`, vedi la sezione seguente) e la
pubblicazione automatica in `.github/workflows/deploy.yml`.
A ogni pubblicazione i fogli di `dati.xlsx` vengono esportati anche in
`data/export/*.csv`, così la cronologia di ogni scheda è consultabile su GitHub.
Le convenzioni tecniche del codice — incluso il registro dei debiti noti —
sono documentate in `documentazione/CONVENZIONI.md`; il sistema grafico del
sito in `DESIGN.md`.

## Gestione del sito: il Launcher

Tutte le operazioni si lanciano dalla radice del progetto con `Launcher.py`,
l'unico punto d'ingresso previsto: gli script in `scripts/` non vanno
lanciati direttamente. Prima installazione delle dipendenze:

```
pip install -r requirements.txt
```

### Menu (doppio click su Launcher.py, oppure `python Launcher.py`)

| Voce | Azione | Cosa fa |
|---|---|---|
| 1 | Controlla i dati | valida `dati.xlsx`; non genera e non pubblica |
| 2 | Anteprima nel browser | rigenera e apre il sito in locale; Ctrl+C per chiudere |
| 3 | Pubblica | rigenera, mostra cosa cambia e chiede conferma prima dell'invio |
| 4 | Rigenera schede e pubblica | chiede gli ID (es. AMI-0034) |
| 5 | Riepilogo dell'ultima generazione | errori e avvisi |
| 6 | Test automatici | da usare dopo modifiche al codice (vedi sotto) |
| 0 | Esci | |

Dopo ogni azione si torna al menu. Rispondendo N (o solo INVIO) alla
conferma, nulla viene inviato a GitHub e le modifiche restano nella cartella.
Se `Launcher.py` viene lanciato da un altro programma (senza terminale
interattivo), pubblica direttamente senza menu né conferma.

### Gli stessi comandi da terminale

```
python Launcher.py --valida                  # come la voce 1
python Launcher.py --anteprima               # come la voce 2
python Launcher.py --test                    # come la voce 6
python Launcher.py --pubblica                # come la voce 3
python Launcher.py --pubblica --si           # pubblica senza chiedere conferma
python Launcher.py "Aggiunta serie 1972-73"  # pubblica con un messaggio di commit scritto a mano
python Launcher.py --only AMI-0034,AMI-0035  # rigenera solo queste schede (anche la cache IA) e pubblica
python Launcher.py --dettagli ...            # mostra a schermo tutto l'output degli script
python Launcher.py --skip-validation ...     # pubblica anche se dati.xlsx ha errori
python Launcher.py --help                    # elenco completo delle opzioni
```

`--only` serve quando una scheda mostra dati sbagliati o non aggiornati
(es. descrizione di Internet Archive cambiata) e vuoi correggerla senza
toccare il resto.

### Controlli senza pubblicare

```
python -m scripts.core.validator    # solo validazione di dati.xlsx: errori, avvisi e note con foglio, riga e colonna
python -m scripts.core.esito        # errori e avvisi dell'ultima generazione
mkdocs build                        # costruisce il sito in site/ ...
python scripts/controlla_sito.py    # ... e ne controlla pagine, sitemap, JSON e link interni
```

Il Launcher esegue da solo validazione, costruzione e controllo prima di ogni
pubblicazione: con un errore, nulla viene inviato a GitHub.

### Test automatici

Servono dopo una modifica al codice (script, generatori), non dopo una
modifica ai dati. Sono due:

- **Test di base** (`tests/test_*.py`, `python -m unittest discover -s tests -t .`):
  convenzioni delle date («ca.», «s.d.», formati italiani), validatore,
  messaggi di commit. Girano anche su GitHub prima di ogni pubblicazione:
  se falliscono il sito non viene aggiornato.
- **Confronto con il sito di riferimento** (`python -m tests.confronto`): genera
  il sito da un piccolo estratto fisso del catalogo (`tests/dati_prova.xlsx`,
  senza collegamenti a Internet Archive) e lo confronta con quello salvato in
  `tests/riferimento/`, mostrando le pagine cambiate. Se il cambiamento è
  voluto (es. hai modificato come una scheda mostra le date) il Launcher
  chiede se aggiornare il riferimento (`python -m tests.confronto --aggiorna`);
  se non è voluto, hai trovato un effetto collaterale prima di pubblicarlo.
  Gira solo in locale.

### Cache di Internet Archive

```
python Launcher.py --refresh-ia identifier1,identifier2   # riscarica solo questi item
python Launcher.py --force-refresh-ia                     # riscarica tutto
python Launcher.py --clear-cache                          # svuota tutta la cache
python Launcher.py --cache-stats                          # statistiche della cache
```

`--refresh-ia` non invalida la cache delle schede: per correggere del tutto
una singola scheda usa `--only`.

### Come lavora il Launcher

- **Registro:** a schermo ogni fase occupa una riga (esito e durata);
  l'output completo è salvato in `log/launcher_AAAA-MM-GG_HH-MM-SS.log`
  (si tengono gli ultimi 30; `log/` non viene pubblicata). Se una fase
  fallisce compaiono le sue ultime righe e il percorso del registro.
- **Excel aperto:** se trova `data/~$dati.xlsx` (il file che Excel crea
  mentre `dati.xlsx` è aperto) il Launcher ricorda di salvare: usa solo
  l'ultima versione salvata.
- **Ripartenza da zero:** `build/` e `site/` vengono svuotate e rigenerate
  a ogni esecuzione, come su GitHub Actions.
- **Commit selettivo:** vengono pubblicati solo i percorsi elencati in
  `PERCORSI_PUBBLICATI` (in testa a `Launcher.py`); gli altri file
  modificati vengono segnalati ma non inviati.
- **Export CSV e messaggi di commit:** i fogli di `dati.xlsx` vengono
  esportati in `data/export/*.csv` (da non modificare a mano: la fonte è
  l'xlsx). Il confronto con l'ultima versione genera il messaggio di commit,
  es. «Dati: Catalogo +2 ~1 (AMI-0097, AMI-0098, AMI-0034)». Per la storia di
  una scheda su GitHub: apri `data/export/catalogo.csv` e usa «History» o «Blame».
- **Sincronizzazione:** prima dell'invio il Launcher esegue
  `git pull --rebase --autostash`, così modifiche fatte altrove (es. su
  GitHub) vengono recuperate senza operazioni manuali.
- **Versione di Python:** quella indicata in `.python-version`, la stessa
  usata da GitHub Actions; il Launcher avvisa se quella locale è diversa.

## Contributi

AMI è un progetto aperto al contributo di studiosi, archivisti, ricercatori e appassionati di storia contemporanea.

Sono benvenuti:

* segnalazioni di documenti mancanti;
* correzioni dei dati descrittivi;
* suggerimenti metodologici;
* contributi per l'ampliamento del catalogo.

Per proporre modifiche è possibile aprire una issue o inviare una pull request.

## Licenza

I contenuti del progetto sono distribuiti secondo le condizioni indicate nei singoli materiali e nelle relative fonti di provenienza.

La responsabilità dei diritti d'autore dei documenti digitalizzati rimane attribuita ai rispettivi detentori.

## Contatti

Per informazioni, collaborazioni o segnalazioni:

* Repository: https://github.com/ami-aim/archivio-maoismo-italiano
* Sito web: https://ami-aim.github.io/archivio-maoismo-italiano/

\---

**AMI — Archivio del Maoismo Italiano**
Un progetto di storia digitale per la conservazione e lo studio delle fonti del maoismo in Italia.

