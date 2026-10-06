"""
Launcher AMI — aggiorna e pubblica il sito.

Uso:
    python Launcher.py                          Menu (doppio click): controlla, anteprima, pubblica...
                                                Se non c'è un terminale interattivo: pubblica.
    python Launcher.py --pubblica               Rigenera e pubblica (chiede conferma prima del push)
    python Launcher.py "messaggio commit"       Rigenera e pubblica con messaggio custom
    python Launcher.py --valida                 Controlla solo data/dati.xlsx (non genera, non pubblica)
    python Launcher.py --anteprima              Rigenera e apre il sito nel browser (non pubblica)
    python Launcher.py --si ...                 Pubblica senza chiedere conferma
    python Launcher.py --only AMI-0034          Rigenera SOLO le schede indicate (invalida cache
                                                metadati documento + cache IA collegata), poi pubblica
    python Launcher.py --refresh-ia ID1,ID2     Invalida la cache IA solo per gli identifier indicati,
                                                poi rigenera e pubblica
    python Launcher.py --force-refresh-ia       Invalida TUTTA la cache IA (metadati + testi),
                                                poi rigenera e pubblica
    python Launcher.py --clear-cache            Svuota tutta la cache (IA, hash file, metadati doc)
    python Launcher.py --cache-stats            Mostra statistiche cache
    python Launcher.py --skip-validation        Salta la validazione dati (scripts/core/validator.py)
                                                e pubblica comunque anche se ci sono errori
    python Launcher.py --help                   Mostra questo messaggio

Nota: prima di rigenerare il sito, il Launcher esegue sempre la validazione
di data/dati.xlsx (scripts/core/validator.py). Se la validazione fallisce,
la pubblicazione viene bloccata, a meno di usare --skip-validation.

Sequenza di generazione, speculare a .github/workflows/deploy.yml:
    sync_assets -> persone -> org -> generatore -> argomenti -> galleria
    -> mkdocs build -> controlla_sito (pagine, sitemap, JSON, link interni)

Dati in CSV e messaggio di commit: dopo la validazione ogni foglio di
dati.xlsx viene esportato in data/export/*.csv (scripts/core/export_dati.py).
Il confronto con l'ultimo commit genera il messaggio, es.
"Dati: Catalogo +2 ~1 (AMI-0097, AMI-0098, AMI-0034)"; un messaggio passato
a mano diventa il titolo e il riepilogo finisce nel corpo del commit.

Commit selettivo: vengono aggiunti solo i percorsi elencati in
PERCORSI_PUBBLICATI; i file modificati altrove vengono segnalati ma NON
committati (evita di pubblicare per sbaglio file temporanei o di lavoro).
"""

import os
import re
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from scripts.core import esito
from scripts.core.cache_manager import CacheManager
from scripts.core.export_dati import esporta_e_riepiloga
from scripts.core.site_config import SITE_URL
from scripts.core.validator import run_validation

ROOT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
# Material for MkDocs stampa un lungo avviso su MkDocs 2.0: requirements.txt
# blocca già mkdocs<2, quindi lo silenziamo.
ENV_MKDOCS = {"NO_MKDOCS_2_WARNING": "true"}

# Unici percorsi che il Launcher committa. Per pubblicare un nuovo file o una
# nuova cartella in radice, aggiungerlo qui.
PERCORSI_PUBBLICATI = [
    ".github", ".gitignore", ".gitattributes", ".nojekyll", ".python-version",
    "assets", "data", "overrides", "scripts",
    "mkdocs.yml", "requirements.txt", "Launcher.py",
    "README.md", "comandi.txt", "LICENSE", "DESIGN.md",
]


class ErroreComando(Exception):
    pass


def stampa_titolo(testo):
    print()
    print("=" * 60)
    print(testo)
    print("=" * 60)


def esegui(comando, cwd=None, descrizione=None, env=None):
    """Esegue un comando, mostra l'output in tempo reale, interrompe la sequenza se fallisce."""
    if descrizione:
        stampa_titolo(descrizione)
    anteprima = ' '.join(f'"{c}"' if ' ' in c else c for c in comando)
    print(f"$ {anteprima}")
    risultato = subprocess.run(comando, cwd=cwd or ROOT_DIR,
                               env={**os.environ, **env} if env else None)
    if risultato.returncode != 0:
        raise ErroreComando(
            f"il comando '{' '.join(comando)}' è fallito (codice {risultato.returncode})."
        )


def verifica_versione_python():
    """Avvisa se il Python locale non è quello di .python-version (usato da GitHub Actions)."""
    file_versione = ROOT_DIR / ".python-version"
    if not file_versione.exists():
        return
    attesa = file_versione.read_text(encoding="utf-8").strip()
    locale = f"{sys.version_info.major}.{sys.version_info.minor}"
    if locale == attesa:
        print(f"Python {locale} (uguale a GitHub Actions)")
    else:
        print(f"ATTENZIONE: Python locale {locale}, GitHub Actions usa {attesa} "
              "(.python-version). Il sito potrebbe comportarsi diversamente online: "
              f"installa Python {attesa} oppure aggiorna .python-version.")


def verifica_dipendenze():
    stampa_titolo("Verifica dipendenze")
    verifica_versione_python()
    mancanti = []
    requirements_path = ROOT_DIR / "requirements.txt"
    mappa_moduli = {
        "pandas": "pandas",
        "openpyxl": "openpyxl",
        "mkdocs-material": "material",
        "Pillow": "PIL",
    }
    if requirements_path.exists():
        pacchetti = [
            riga.strip() for riga in requirements_path.read_text(encoding="utf-8").splitlines()
            if riga.strip() and not riga.strip().startswith("#")
        ]
    else:
        print(f"'{requirements_path.name}' non trovato, uso elenco di fallback.")
        pacchetti = list(mappa_moduli.keys())

    for requisito in pacchetti:
        # "pandas>=2.2,<4" -> "pandas": i vincoli di versione li gestisce pip.
        pacchetto = re.split(r"[<>=!~;\[ ]", requisito, maxsplit=1)[0].strip()
        modulo = mappa_moduli.get(pacchetto, pacchetto.replace("-", "_"))
        try:
            __import__(modulo)
            print(f"{pacchetto}")
        except ImportError:
            print(f"{pacchetto} non installato")
            mancanti.append(pacchetto)

    if shutil.which("git"):
        print("git")
    else:
        print("git non trovato nel PATH")
        mancanti.append("git")

    if mancanti:
        msg = f"mancano le dipendenze: {', '.join(mancanti)}."
        if "git" in mancanti:
            msg += "\n   Installa git dal sito ufficiale per il tuo sistema operativo."
        pacchetti_pip = [m for m in mancanti if m != "git"]
        if pacchetti_pip:
            msg += "\n   Installa il resto con: pip install -r requirements.txt"
        raise ErroreComando(msg)


def percorsi_esistenti():
    return [p for p in PERCORSI_PUBBLICATI if (ROOT_DIR / p).exists()]


def git_stato(percorsi=None):
    """Righe di `git status --porcelain`, eventualmente limitate a `percorsi`."""
    comando = ["git", "status", "--porcelain"]
    if percorsi:
        comando += ["--"] + percorsi
    risultato = subprocess.run(comando, cwd=ROOT_DIR, capture_output=True, text=True)
    return [r for r in risultato.stdout.splitlines() if r.strip()]


def git_ci_sono_modifiche():
    """True se ci sono modifiche nei percorsi pubblicati."""
    return bool(git_stato(percorsi_esistenti()))


def segnala_file_esclusi():
    """Avvisa dei file modificati FUORI da PERCORSI_PUBBLICATI (non committati)."""
    dentro = set(git_stato(percorsi_esistenti()))
    fuori = [r for r in git_stato() if r not in dentro]
    if fuori:
        print("File modificati fuori dai percorsi pubblicati (NON verranno committati):")
        for riga in fuori:
            print(f"   {riga}")


def identifier_ia_per_documento(ami_id):
    """
    Cerca nell'Excel del catalogo l'identifier Internet Archive collegato
    a un documento AMI, per poter invalidare anche la cache IA in --only.

    Returns:
        str o None se non trovato / url mancante.
    """
    try:
        from scripts.core.dati import leggi_foglio
        df = leggi_foglio('Catalogo')
        riga = df[df['id'].astype(str).str.strip() == ami_id]
        if riga.empty:
            return None
        url = str(riga.iloc[0].get('url', '')).strip()
        match = re.search(r'/details/([^/?#]+)', url)
        return match.group(1) if match else None
    except Exception as e:
        print(f"Impossibile leggere l'identifier IA per {ami_id}: {e}")
        return None


def esegui_validazione(bloccante=True):
    """
    Esegue la validazione dei dati (data/dati.xlsx) tramite
    scripts.core.validator prima di rigenerare il sito.

    Args:
        bloccante: Se True (default), interrompe l'aggiornamento se la
            validazione fallisce. Se False, mostra comunque il report ma
            prosegue (utile con --skip-validation).
    """
    stampa_titolo("Validazione dati (data/dati.xlsx)")
    esito = run_validation(str(ROOT_DIR / "data"))

    if esito.get('error'):
        messaggio = f"Impossibile completare la validazione: {esito['error']}"
        if bloccante:
            raise ErroreComando(messaggio)
        print(f"{messaggio} (proseguo comunque, --skip-validation attivo)")
        return

    if not esito.get('success', False):
        if bloccante:
            raise ErroreComando(
                "la validazione dei dati è fallita (vedi errori sopra). "
                "Correggi data/dati.xlsx oppure rilancia con --skip-validation per pubblicare comunque."
            )
        print("Validazione fallita, ma proseguo comunque (--skip-validation attivo).")
    else:
        print("Dati validati correttamente.")


def git_sync_pubblicazione(titolo, corpo):
    """Sincronizza e pubblica: pull rebase -> add -> commit -> push.

    Il `git pull --rebase --autostash` iniziale recupera eventuali commit
    fatti altrove (es. merge su GitHub del ramo di lavoro, o un secondo
    aggiornamento) ed evita il rifiuto del push con storia divergente. In caso
    di conflitto irrisolvibile il comando fallisce: ErroreComando blocca la
    sequenza e il commit locale resta integro, pronto per essere risolto a
    mano.
    """
    # 1. Recupera gli aggiornamenti remoti RIAPPLICANDO i commit locali sopra
    #    (niente merge commit; --autostash protegge da worktree sporco).
    #    Non usare descrizione: non deve rientrare nel blocco "Git ...".
    esegui(["git", "pull", "--rebase", "--autostash"],
           descrizione="Sincronizzazione col remoto (rebase)")

    # 2. Commit delle modifiche (se ancora presenti dopo il pull), limitato
    #    ai PERCORSI_PUBBLICATI.
    if not git_ci_sono_modifiche():
        print("Nessuna modifica da committare dopo la sincronizzazione.")
        return False
    esegui(["git", "add", "-A", "--"] + percorsi_esistenti(), descrizione="Git add")
    comando_commit = ["git", "commit", "-m", titolo]
    if corpo:
        comando_commit += ["-m", corpo]
    esegui(comando_commit, descrizione="Git commit")

    # 3. Push.
    esegui(["git", "push"], descrizione="Git push")
    return True


# Impostati in aggiorna(): messaggio scritto a mano e riepilogo dei dati.
messaggio_globale = {"testo": None, "dati_titolo": None, "dati_corpo": None}


def aree_modificate():
    """Cartelle/file di primo livello modificati, esclusi i dati (es. 'scripts, assets')."""
    aree = []
    for riga in git_stato(percorsi_esistenti()):
        percorso = riga[3:].strip().strip('"').split(" -> ")[-1]
        area = percorso.split("/")[0]
        if area != "data" and area not in aree:
            aree.append(area)
    return aree


def componi_messaggio_commit():
    """(titolo, corpo) del commit.

    - messaggio a mano  -> titolo = messaggio, corpo = riepilogo dati;
    - dati cambiati      -> titolo = riepilogo dati ("Dati: Catalogo +1 ...");
    - solo codice/asset  -> "Aggiornamento sito: scripts, assets — data ora".
    """
    data_ora = datetime.now().strftime('%d/%m/%Y %H:%M')
    dati_titolo = messaggio_globale["dati_titolo"]
    dati_corpo = messaggio_globale["dati_corpo"]
    aree = aree_modificate()
    righe_corpo = []
    if dati_corpo:
        righe_corpo.append(dati_corpo)
    if aree:
        righe_corpo.append("Altri file: " + ", ".join(aree))

    if messaggio_globale["testo"]:
        if dati_titolo:
            righe_corpo.insert(0, dati_titolo)
        return messaggio_globale["testo"], "\n".join(righe_corpo)
    if dati_titolo:
        return dati_titolo, "\n".join(righe_corpo)
    if aree:
        return f"Aggiornamento sito: {', '.join(aree)} — {data_ora}", ""
    return f"Aggiornamento automatico del sito — {data_ora}", ""


def prepara(skip_validation=False, esporta=True):
    """Dipendenze, validazione e (per la pubblicazione) export CSV dei dati."""
    # Riepilogo errori/avvisi: si riparte da zero a ogni esecuzione.
    esito.azzera_riepilogo()
    verifica_dipendenze()

    # Validazione dei dati (blocca se ci sono errori)
    esegui_validazione(bloccante=not skip_validation)

    if not esporta:
        return
    # Export CSV dei fogli + riepilogo modifiche (messaggio di commit)
    stampa_titolo("Export CSV dei dati (data/export/)")
    try:
        titolo, corpo = esporta_e_riepiloga(ROOT_DIR)
    except Exception as e:
        raise ErroreComando(f"export CSV di dati.xlsx non riuscito: {e}")
    messaggio_globale["dati_titolo"] = titolo
    messaggio_globale["dati_corpo"] = corpo


def invalida_cache(only=None, refresh_ia=None):
    # Rigenerazione mirata di specifiche schede documento
    if only:
        stampa_titolo("Rigenerazione mirata")
        cache_mgr = CacheManager()
        cache_mgr.clear_doc_metadata(only)
        identifiers = [i for i in (identifier_ia_per_documento(d) for d in only) if i]
        if identifiers:
            cache_mgr.clear_ia_metadata(identifiers)
            print(f"Verranno rigenerate: {', '.join(only)} (IA: {', '.join(identifiers)})")
        else:
            print(f"Verranno rigenerate: {', '.join(only)} (nessun identifier IA trovato/collegato)")

    # Invalidazione mirata/globale cache IA, se richiesta a parte
    if refresh_ia:
        stampa_titolo("Invalidazione cache Internet Archive")
        cache_mgr = CacheManager()
        if refresh_ia == 'all':
            cache_mgr.clear_ia_metadata()
            print("Tutti i documenti verranno ri-scaricati da Internet Archive.")
        else:
            cache_mgr.clear_ia_metadata(refresh_ia)
            print(f"Verranno ri-scaricati solo: {', '.join(refresh_ia)}")


def genera_sito():
    """Generazione completa in build/, mkdocs build in site/ e controllo finale."""
    # Sincronizzazione file statici (deve girare per primo)
    esegui([sys.executable, "sync_assets.py"], cwd=SCRIPTS_DIR,
           descrizione="Sincronizzazione file statici (assets/ → build/)")

    # Rigenerazione contenuti.
    # Ordine: persone/org PRIMA di generatore; argomenti DOPO generatore,
    # così argomenti.py può aggiornare la sitemap appena creata;
    # galleria DOPO argomenti, come in .github/workflows/deploy.yml.
    esegui([sys.executable, "persone.py"], cwd=SCRIPTS_DIR,
           descrizione="Generazione schede persone")
    esegui([sys.executable, "org.py"], cwd=SCRIPTS_DIR,
           descrizione="Generazione schede organizzazioni")
    esegui([sys.executable, "generatore.py"], cwd=SCRIPTS_DIR,
           descrizione="Generazione documenti, archivio, home, sitemap")
    esegui([sys.executable, "argomenti.py"], cwd=SCRIPTS_DIR,
           descrizione="Generazione pagine argomenti")
    esegui([sys.executable, "galleria.py"], cwd=SCRIPTS_DIR,
           descrizione="Generazione galleria fotografica (build/galleria/)")

    # Costruzione del sito e controllo finale (pagine, sitemap, JSON, link
    # interni): gli stessi controlli girano su GitHub Actions prima del
    # deploy, ma qui un problema blocca la pubblicazione PRIMA del push.
    esegui([sys.executable, "-m", "mkdocs", "build", "--quiet"],
           descrizione="Costruzione del sito (mkdocs build -> site/)",
           env=ENV_MKDOCS)
    esegui([sys.executable, str(SCRIPTS_DIR / "controlla_sito.py"), str(ROOT_DIR / "site")],
           descrizione="Controllo del sito generato")

    stampa_riepilogo_build()


def interattivo():
    """True se c'è una persona davanti al terminale (doppio click, cmd...)."""
    try:
        return sys.stdin.isatty()
    except (AttributeError, ValueError):
        return False


def chiedi(domanda):
    try:
        return input(domanda).strip()
    except EOFError:
        return ""


def conferma_pubblicazione(titolo, corpo, chiedi_conferma=True):
    """Mostra cosa sta per essere pubblicato e, se richiesto, chiede conferma.

    Senza terminale interattivo (es. lancio da un altro programma) o con
    --si non chiede nulla e prosegue, come faceva il Launcher prima.
    """
    stampa_titolo("Cosa verrà pubblicato")
    print(titolo)
    if corpo:
        for riga in corpo.splitlines():
            print(f"  {riga}")
    print()
    righe = git_stato(percorsi_esistenti())
    print(f"File modificati ({len(righe)}):")
    for riga in righe[:25]:
        print(f"  {riga}")
    if len(righe) > 25:
        print(f"  ... e altri {len(righe) - 25}")
    segnala_file_esclusi()
    voci = esito.leggi_riepilogo()
    avvisi = sum(v["gravita"] == esito.AVVISO for v in voci)
    if avvisi:
        print(f"\nNota: la generazione ha prodotto {avvisi} avvisi (vedi il riepilogo sopra).")

    if not chiedi_conferma:
        return True
    if not interattivo():
        print("\n(Esecuzione non interattiva: pubblico senza chiedere conferma.)")
        return True
    risposta = chiedi("\nPubblicare queste modifiche su GitHub? [s/N] ").lower()
    return risposta in ("s", "si", "sì", "y", "yes")


def pubblica(messaggio=None, chiedi_conferma=True):
    """Commit e push delle modifiche (dopo prepara() e genera_sito())."""
    stampa_titolo("Pubblicazione")
    if not git_ci_sono_modifiche():
        print("Nessuna modifica rispetto all'ultimo commit: niente da pubblicare.")
        stampa_titolo("Completato (nessuna modifica)")
        return False

    messaggio_globale["testo"] = messaggio  # None -> messaggio automatico
    titolo, corpo = componi_messaggio_commit()
    if not conferma_pubblicazione(titolo, corpo, chiedi_conferma):
        stampa_titolo("Pubblicazione annullata")
        print("Niente è stato inviato a GitHub: le modifiche restano nella cartella,")
        print("pronte per la prossima pubblicazione.")
        return False

    if not git_sync_pubblicazione(titolo, corpo):
        return False
    stampa_titolo("Sito aggiornato e pubblicato!")
    print("GitHub Actions builderà e pubblicherà automaticamente su GitHub Pages")
    print("(di solito ci vuole qualche minuto prima che sia visibile online).")
    return True


def aggiorna(messaggio=None, refresh_ia=None, only=None, skip_validation=False,
             chiedi_conferma=True):
    stampa_titolo("Aggiornamento del sito AMI")
    prepara(skip_validation=skip_validation)
    invalida_cache(only=only, refresh_ia=refresh_ia)
    genera_sito()
    pubblica(messaggio, chiedi_conferma=chiedi_conferma)


def solo_validazione():
    """Controlla dati.xlsx e basta: nessuna generazione, nessuna pubblicazione."""
    stampa_titolo("Controllo dei dati (data/dati.xlsx)")
    risultato = run_validation(str(ROOT_DIR / "data"))
    if risultato.get("error"):
        raise ErroreComando(f"impossibile leggere i dati: {risultato['error']}")
    print()
    if risultato.get("success"):
        print("Nessun errore: i dati possono essere pubblicati.")
    else:
        print("Ci sono errori da correggere in dati.xlsx prima di pubblicare (vedi sopra).")
    return risultato.get("success", False)


def _porta_libera():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def anteprima(skip_validation=False):
    """Rigenera il sito e lo apre nel browser con `mkdocs serve`. Non pubblica."""
    stampa_titolo("Anteprima del sito AMI")
    prepara(skip_validation=skip_validation, esporta=False)
    genera_sito()

    porta = _porta_libera()
    percorso = urlparse(SITE_URL).path.rstrip("/") + "/"
    indirizzo = f"http://127.0.0.1:{porta}{percorso}"
    stampa_titolo("Anteprima in corso")
    print(f"Il sito è visibile su {indirizzo}")
    print("Si aggiorna da solo se rigeneri il sito (es. dal menu in un'altra finestra).")
    print("Per chiudere l'anteprima premi Ctrl+C.\n")
    processo = subprocess.Popen(
        [sys.executable, "-m", "mkdocs", "serve", "--quiet", "-a", f"127.0.0.1:{porta}"],
        cwd=ROOT_DIR, env={**os.environ, **ENV_MKDOCS})
    interrotto = False
    try:
        time.sleep(3)
        if processo.poll() is None:
            webbrowser.open(indirizzo)
        processo.wait()
    except KeyboardInterrupt:
        interrotto = True
        print("\nChiusura dell'anteprima...")
    finally:
        if processo.poll() is None:
            processo.terminate()
            try:
                processo.wait(timeout=10)
            except subprocess.TimeoutExpired:
                processo.kill()
    if not interrotto and processo.returncode:
        raise ErroreComando(f"l'anteprima (mkdocs serve) si è chiusa con codice "
                            f"{processo.returncode}: vedi i messaggi sopra")
    print("Anteprima chiusa.")


def stampa_riepilogo_build():
    """Riepilogo di errori e avvisi raccolti dagli script di generazione."""
    voci = esito.leggi_riepilogo()
    stampa_titolo("Riepilogo errori e avvisi della generazione")
    print(esito.formatta_riepilogo(voci))


def mostra_cache_stats():
    """Mostra statistiche cache."""
    stampa_titolo("Statistiche Cache")
    cache_mgr = CacheManager()
    cache_mgr.print_stats()


def svuota_cache():
    """Svuota cache."""
    stampa_titolo("Pulizia Cache")
    cache_mgr = CacheManager()
    cache_mgr.clear_all()
    print("Cache completamente svuotata")


# ---------------------------------------------------------------------------
# Menu (doppio click sul Launcher)
# ---------------------------------------------------------------------------

VOCI_MENU = [
    ("1", "Controlla i dati (dati.xlsx)", "non genera e non pubblica"),
    ("2", "Anteprima del sito nel browser", "rigenera, non pubblica"),
    ("3", "Pubblica", "rigenera, mostra le modifiche e chiede conferma"),
    ("4", "Rigenera schede specifiche e pubblica", "es. AMI-0034"),
    ("5", "Riepilogo errori e avvisi dell'ultima generazione", ""),
    ("0", "Esci", ""),
]


def chiedi_id_schede():
    testo = chiedi("ID delle schede da rigenerare (es. AMI-0034, AMI-0035): ")
    ids = [i.strip().upper() for i in re.split(r"[,;\s]+", testo) if i.strip()]
    errati = [i for i in ids if not re.fullmatch(r"AMI-\d{4,}", i)]
    if errati:
        print(f"ID non validi: {', '.join(errati)} (formato atteso: AMI-0034)")
        return None
    return ids or None


def menu():
    while True:
        print()
        print("=" * 60)
        print("AMI — Archivio del Maoismo Italiano")
        print("=" * 60)
        for tasto, voce, nota in VOCI_MENU:
            print(f"  {tasto}  {voce}" + (f"  ({nota})" if nota else ""))
        try:
            scelta = input("\nScelta: ").strip()
        except EOFError:
            return
        if not scelta:
            continue
        if scelta in ("0", "q"):
            return
        try:
            if scelta == "1":
                solo_validazione()
            elif scelta == "2":
                anteprima()
            elif scelta == "3":
                aggiorna()
            elif scelta == "4":
                ids = chiedi_id_schede()
                if ids:
                    aggiorna(only=ids)
            elif scelta == "5":
                stampa_riepilogo_build()
            else:
                print("Scelta non valida.")
                continue
        except ErroreComando as e:
            if esito.leggi_riepilogo() and scelta in ("2", "3", "4"):
                stampa_riepilogo_build()
            print(f"\nERRORE: {e}")
            if scelta in ("3", "4"):
                print("Il sito NON è stato pubblicato.")
        except KeyboardInterrupt:
            print("\n\nInterrotto: torno al menu.")
        chiedi("\nPremi INVIO per tornare al menu...")


def main():
    args = sys.argv[1:]
    if not args and interattivo():
        try:
            menu()
        except KeyboardInterrupt:
            pass
        sys.exit(0)

    codice_uscita = 0
    try:
        refresh_ia = None
        only = None
        messaggio = None

        skip_validation = '--skip-validation' in args
        chiedi_conferma = '--si' not in args
        args = [a for a in args if a not in ('--skip-validation', '--si', '--pubblica')]

        if args:
            if args[0] == '--clear-cache':
                svuota_cache()
                return
            elif args[0] == '--cache-stats':
                mostra_cache_stats()
                return
            elif args[0] == '--help':
                print(__doc__)
                return
            elif args[0] == '--valida':
                codice_uscita = 0 if solo_validazione() else 1
                return
            elif args[0] == '--anteprima':
                anteprima(skip_validation=skip_validation)
                return
            elif args[0] == '--force-refresh-ia':
                refresh_ia = 'all'
                args = args[1:]
            elif args[0] == '--refresh-ia':
                if len(args) < 2:
                    print("Uso: python Launcher.py --refresh-ia <identifier1,identifier2,...>")
                    return
                refresh_ia = [i.strip() for i in args[1].split(',') if i.strip()]
                args = args[2:]
            elif args[0] == '--only':
                if len(args) < 2:
                    print("Uso: python Launcher.py --only <AMI-0001,AMI-0002,...>")
                    return
                only = [i.strip() for i in args[1].split(',') if i.strip()]
                args = args[2:]

            if args and not args[0].startswith('--'):
                messaggio = args[0]

        aggiorna(messaggio=messaggio, refresh_ia=refresh_ia, only=only,
                 skip_validation=skip_validation, chiedi_conferma=chiedi_conferma)

    except ErroreComando as e:
        if esito.leggi_riepilogo():
            stampa_riepilogo_build()
        print(f"\nERRORE: {e}")
        print("Il sito NON è stato pubblicato: correggi l'errore sopra e rilancia lo script.")
        codice_uscita = 1
    except KeyboardInterrupt:
        print("\n\nInterrotto manualmente.")
        codice_uscita = 1
    finally:
        if interattivo():
            print()
            chiedi("Premi INVIO per chiudere...")

    sys.exit(codice_uscita)


if __name__ == "__main__":
    main()
