"""
Launcher AMI — aggiorna e pubblica il sito.

Uso:
    python Launcher.py                          Rigenera e pubblica (con messaggio commit automatico)
    python Launcher.py "messaggio commit"       Rigenera e pubblica con messaggio custom
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
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from scripts.core import esito
from scripts.core.cache_manager import CacheManager
from scripts.core.export_dati import esporta_e_riepiloga
from scripts.core.validator import run_validation

ROOT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT_DIR / "scripts"

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


def git_sync_pubblicazione():
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
    segnala_file_esclusi()
    titolo, corpo = componi_messaggio_commit()
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


def aggiorna(messaggio=None, refresh_ia=None, only=None, skip_validation=False):
    stampa_titolo("Aggiornamento del sito AMI")
    # Riepilogo errori/avvisi: si riparte da zero a ogni esecuzione.
    esito.azzera_riepilogo()
    verifica_dipendenze()

    # 0bis. Validazione dei dati (blocca la pubblicazione se ci sono errori)
    esegui_validazione(bloccante=not skip_validation)

    # 0ter. Export CSV dei fogli + riepilogo modifiche (messaggio di commit)
    stampa_titolo("Export CSV dei dati (data/export/)")
    try:
        titolo, corpo = esporta_e_riepiloga(ROOT_DIR)
    except Exception as e:
        raise ErroreComando(f"export CSV di dati.xlsx non riuscito: {e}")
    messaggio_globale["dati_titolo"] = titolo
    messaggio_globale["dati_corpo"] = corpo

    # -1. Rigenerazione mirata di specifiche schede documento
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

    # -1bis. Invalidazione mirata/globale cache IA, se richiesta a parte
    if refresh_ia:
        stampa_titolo("Invalidazione cache Internet Archive")
        cache_mgr = CacheManager()
        if refresh_ia == 'all':
            cache_mgr.clear_ia_metadata()
            print("Tutti i documenti verranno ri-scaricati da Internet Archive.")
        else:
            cache_mgr.clear_ia_metadata(refresh_ia)
            print(f"Verranno ri-scaricati solo: {', '.join(refresh_ia)}")

    # 0. Sincronizzazione file statici (deve girare per primo)
    esegui([sys.executable, "sync_assets.py"], cwd=SCRIPTS_DIR,
           descrizione="Sincronizzazione file statici (assets/ → build/)")

    # 1-5. Rigenerazione contenuti.
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

    # 7. Costruzione del sito e controllo finale (pagine, sitemap, JSON, link
    #    interni): gli stessi controlli girano su GitHub Actions prima del
    #    deploy, ma qui un problema blocca la pubblicazione PRIMA del push.
    esegui([sys.executable, "-m", "mkdocs", "build", "--quiet"],
           descrizione="Costruzione del sito (mkdocs build -> site/)",
           env={"NO_MKDOCS_2_WARNING": "true"})
    esegui([sys.executable, str(SCRIPTS_DIR / "controlla_sito.py"), str(ROOT_DIR / "site")],
           descrizione="Controllo del sito generato")

    stampa_riepilogo_build()

    # 6. Pubblicazione (pull --rebase -> add -> commit -> push)
    stampa_titolo("Pubblicazione")
    if not git_ci_sono_modifiche():
        print("Nessuna modifica rispetto all'ultimo commit: niente da pubblicare.")
        stampa_titolo("Completato (nessuna modifica)")
        return

    messaggio_globale["testo"] = messaggio  # None -> messaggio automatico
    git_sync_pubblicazione()

    stampa_titolo("Sito aggiornato e pubblicato!")
    print("GitHub Actions builderà e pubblicherà automaticamente su GitHub Pages")
    print("(di solito ci vuole qualche minuto prima che sia visibile online).")


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


def main():
    codice_uscita = 0
    try:
        args = sys.argv[1:]
        refresh_ia = None
        only = None
        messaggio = None

        skip_validation = '--skip-validation' in args
        if skip_validation:
            args = [a for a in args if a != '--skip-validation']

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
                 skip_validation=skip_validation)

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
        print()
        try:
            input("Premi INVIO per chiudere...")
        except EOFError:
            pass

    sys.exit(codice_uscita)


if __name__ == "__main__":
    main()