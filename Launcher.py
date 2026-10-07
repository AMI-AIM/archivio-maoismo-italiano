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
    python Launcher.py --dettagli ...           Mostra a schermo tutto l'output degli script
                                                (di norma va nel registro log/launcher_*.log)
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

Interfaccia (scripts/core/interfaccia.py): ogni fase occupa una riga con
esito e durata; l'output dettagliato va in log/ (ultimi 30 registri). Se una
fase fallisce compaiono le sue ultime righe e il percorso del registro.

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
from scripts.core.interfaccia import ErroreComando, Interfaccia
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
    "README.md", "LICENSE", "DESIGN.md", "documentazione",
]

# Interfaccia a terminale; main() la ricrea con --dettagli se richiesto.
ui = Interfaccia(ROOT_DIR)

# Impostati durante l'esecuzione: messaggio scritto a mano e riepilogo dei dati.
messaggio_globale = {"testo": None, "dati_titolo": None, "dati_corpo": None}


# ---------------------------------------------------------------------------
# Controlli preliminari
# ---------------------------------------------------------------------------

def versione_python_diversa():
    """Messaggio se il Python locale non è quello di .python-version, altrimenti None."""
    file_versione = ROOT_DIR / ".python-version"
    if not file_versione.exists():
        return None
    attesa = file_versione.read_text(encoding="utf-8").strip()
    locale = f"{sys.version_info.major}.{sys.version_info.minor}"
    if locale == attesa:
        return None
    return (f"Python locale {locale}, GitHub Actions usa {attesa} (.python-version): "
            f"installa Python {attesa} oppure aggiorna .python-version.")


def verifica_dipendenze():
    with ui.fase("Dipendenze") as stato:
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
            pacchetti = list(mappa_moduli.keys())

        for requisito in pacchetti:
            # "pandas>=2.2,<4" -> "pandas": i vincoli di versione li gestisce pip.
            pacchetto = re.split(r"[<>=!~;\[ ]", requisito, maxsplit=1)[0].strip()
            modulo = mappa_moduli.get(pacchetto, pacchetto.replace("-", "_"))
            try:
                __import__(modulo)
            except ImportError:
                mancanti.append(pacchetto)
        if not shutil.which("git"):
            mancanti.append("git")

        if mancanti:
            msg = f"mancano le dipendenze: {', '.join(mancanti)}."
            if "git" in mancanti:
                msg += " Installa git dal sito ufficiale."
            if [m for m in mancanti if m != "git"]:
                msg += " Installa il resto con: pip install -r requirements.txt"
            raise ErroreComando(msg)
        stato["dettaglio"] = f"Python {sys.version_info.major}.{sys.version_info.minor}"
    differenza = versione_python_diversa()
    if differenza:
        ui.avviso(differenza)


def _conta(n, singolare, plurale):
    return f"{n} {singolare if n == 1 else plurale}"


def _riepilogo_validazione(r):
    return (f"{_conta(r.get('errori', 0), 'errore', 'errori')} · "
            f"{_conta(r.get('avvisi', 0), 'avviso', 'avvisi')} · "
            f"{_conta(r.get('note', 0), 'nota', 'note')}")


def _voci_validazione(voci, includi_note=False):
    """Stampa errori, avvisi (e note) della validazione, indentati e colorati."""
    stili = {"errore": "errore", "avviso": "avviso", "nota": "nota"}
    for v in voci:
        if v["gravita"] == "nota" and not includi_note:
            continue
        posizione = ", ".join(str(x) for x in (v["foglio"],
                              f"riga {v['riga']}" if v["riga"] else None, v["colonna"]) if x)
        etichetta = v["gravita"].upper()
        ui.scrivi(f"     [{stili[v['gravita']]}]{etichetta}[/] [tenue]{ui.esc(posizione)}:[/] "
                  f"{ui.esc(v['messaggio'])}"
                  if ui.console else f"     {etichetta} {posizione}: {v['messaggio']}")


def esegui_validazione(bloccante=True):
    """Valida data/dati.xlsx; con errori blocca (salvo --skip-validation)."""
    risultato = {}
    try:
        with ui.fase("Controllo dei dati") as stato:
            risultato = ui.cattura(run_validation, str(ROOT_DIR / "data"))
            if risultato.get("error"):
                raise ErroreComando(f"impossibile leggere i dati: {risultato['error']}")
            stato["dettaglio"] = _riepilogo_validazione(risultato)
            if not risultato.get("success") and bloccante:
                raise ErroreComando(
                    "ci sono errori in data/dati.xlsx: correggili e rilancia "
                    "(oppure usa --skip-validation per pubblicare comunque).")
    finally:
        _voci_validazione(risultato.get("voci", []))
    if not risultato.get("success") and not bloccante:
        ui.avviso("validazione fallita, ma proseguo (--skip-validation attivo)")


# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------

def percorsi_esistenti():
    """Percorsi pubblicati da passare a git: quelli presenti su disco e quelli
    ancora in Git ma cancellati (così anche la cancellazione viene pubblicata)."""
    tracciati = subprocess.run(["git", "ls-files", "--", *PERCORSI_PUBBLICATI], cwd=ROOT_DIR,
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace").stdout.splitlines()
    in_git = {riga.split("/")[0] for riga in tracciati}
    return [p for p in PERCORSI_PUBBLICATI if (ROOT_DIR / p).exists() or p in in_git]


def git_stato(percorsi=None):
    """Righe di `git status --porcelain`, eventualmente limitate a `percorsi`."""
    comando = ["git", "status", "--porcelain"]
    if percorsi:
        comando += ["--"] + percorsi
    risultato = subprocess.run(comando, cwd=ROOT_DIR, capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
    return [r for r in risultato.stdout.splitlines() if r.strip()]


def git_ci_sono_modifiche():
    """True se ci sono modifiche nei percorsi pubblicati."""
    return bool(git_stato(percorsi_esistenti()))


def _fuori_dai_percorsi():
    dentro = set(git_stato(percorsi_esistenti()))
    return [r for r in git_stato() if r not in dentro]


def file_esclusi():
    """File modificati FUORI da PERCORSI_PUBBLICATI (non verranno committati).

    Non conta le modifiche già "preparate" con git (prima colonna di
    `git status` piena, es. un file rimosso con `git rm`): il commit le
    include comunque.
    """
    return [r for r in _fuori_dai_percorsi() if r[0] in " ?"]


def file_preparati_fuori_percorsi():
    """Modifiche già preparate con git fuori dai percorsi: entrano nel commit."""
    return [r for r in _fuori_dai_percorsi() if r[0] not in " ?"]


def git_sync_pubblicazione(titolo, corpo):
    """Sincronizza e pubblica: pull rebase -> add -> commit -> push.

    Il `git pull --rebase --autostash` iniziale recupera eventuali commit
    fatti altrove (es. merge su GitHub del ramo di lavoro, o un secondo
    aggiornamento) ed evita il rifiuto del push con storia divergente. In caso
    di conflitto irrisolvibile il comando fallisce: ErroreComando blocca la
    sequenza e il commit locale resta integro, pronto per essere risolto a
    mano.
    """
    with ui.fase("Sincronizzazione con GitHub"):
        ui.esegui(["git", "pull", "--rebase", "--autostash"])

    if not git_ci_sono_modifiche():
        ui.scrivi("  Nessuna modifica da registrare dopo la sincronizzazione.", "tenue")
        return False
    with ui.fase("Registrazione delle modifiche (commit)") as stato:
        ui.esegui(["git", "add", "-A", "--"] + percorsi_esistenti())
        comando_commit = ["git", "commit", "-m", titolo]
        if corpo:
            comando_commit += ["-m", corpo]
        ui.esegui(comando_commit)
        stato["dettaglio"] = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT_DIR,
            capture_output=True, text=True).stdout.strip()
    with ui.fase("Invio a GitHub (push)"):
        ui.esegui(["git", "push"])
    return True


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


def identifier_ia_per_documento(ami_id):
    """Identifier Internet Archive collegato a un documento AMI (per --only), o None."""
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
        ui.avviso(f"impossibile leggere l'identifier IA per {ami_id}: {e}")
        return None


# ---------------------------------------------------------------------------
# Fasi della pipeline
# ---------------------------------------------------------------------------

def prepara(skip_validation=False, esporta=True):
    """Dipendenze, validazione e (per la pubblicazione) export CSV dei dati."""
    # Riepilogo errori/avvisi: si riparte da zero a ogni esecuzione.
    esito.azzera_riepilogo()
    verifica_dipendenze()
    esegui_validazione(bloccante=not skip_validation)

    if not esporta:
        return
    with ui.fase("Export CSV dei dati") as stato:
        try:
            titolo, corpo = ui.cattura(esporta_e_riepiloga, ROOT_DIR)
        except Exception as e:
            raise ErroreComando(f"export CSV di dati.xlsx non riuscito: {e}")
        stato["dettaglio"] = titolo or "dati invariati"
    messaggio_globale["dati_titolo"] = titolo
    messaggio_globale["dati_corpo"] = corpo


def invalida_cache(only=None, refresh_ia=None):
    if only:
        with ui.fase("Rigenerazione mirata") as stato:
            cache_mgr = ui.cattura(CacheManager)
            ui.cattura(cache_mgr.clear_doc_metadata, only)
            identifiers = [i for i in (identifier_ia_per_documento(d) for d in only) if i]
            if identifiers:
                ui.cattura(cache_mgr.clear_ia_metadata, identifiers)
            stato["dettaglio"] = ", ".join(only)

    if refresh_ia:
        with ui.fase("Cache di Internet Archive svuotata") as stato:
            cache_mgr = ui.cattura(CacheManager)
            if refresh_ia == 'all':
                ui.cattura(cache_mgr.clear_ia_metadata)
                stato["dettaglio"] = "tutti i documenti"
            else:
                ui.cattura(cache_mgr.clear_ia_metadata, refresh_ia)
                stato["dettaglio"] = ", ".join(refresh_ia)


# Ordine: sync_assets per primo; persone/org PRIMA di generatore; argomenti
# DOPO generatore (aggiorna la sitemap appena creata); galleria per ultima,
# come in .github/workflows/deploy.yml.
SCRIPT_GENERAZIONE = [
    ("sync_assets.py", "File statici"),
    ("persone.py", "Schede persone"),
    ("org.py", "Schede organizzazioni"),
    ("generatore.py", "Documenti, archivio, home"),
    ("argomenti.py", "Percorsi tematici"),
    ("galleria.py", "Galleria"),
]


def _avvisi_nuovi(prima):
    voci = esito.leggi_riepilogo()
    nuove = voci[prima:]
    n = sum(v["gravita"] == esito.AVVISO for v in nuove)
    return len(voci), (_conta(n, "avviso", "avvisi") if n else "")


def svuota_cartelle_generate():
    """Svuota build/ e site/ prima di generare: si parte da zero come su GitHub.

    Senza questa pulizia vi restavano file che il codice non produce più
    (vecchi font, immagini dei percorsi in PNG, JSON a blocchi): finivano
    nell'anteprima locale e potevano nascondere un'immagine mancante in
    assets/, perché argomenti.py la cerca anche in build/.
    """
    with ui.fase("Pulizia di build/ e site/"):
        for nome in ("build", "site"):
            cartella = ROOT_DIR / nome
            if not cartella.exists():
                continue
            try:
                shutil.rmtree(cartella)
            except OSError as e:
                raise ErroreComando(
                    f"impossibile svuotare {nome}/ ({e}). Se l'anteprima è aperta in un'altra "
                    "finestra, chiudila (Ctrl+C) e riprova.")


def genera_sito():
    """Generazione completa in build/, mkdocs build in site/ e controllo finale."""
    svuota_cartelle_generate()
    voci_lette = 0
    for script, nome in SCRIPT_GENERAZIONE:
        with ui.fase(nome) as stato:
            try:
                ui.esegui([sys.executable, script], cwd=SCRIPTS_DIR)
            finally:
                voci_lette, stato["dettaglio"] = _avvisi_nuovi(voci_lette)

    # Costruzione del sito e controllo finale (pagine, sitemap, JSON, link
    # interni): gli stessi controlli girano su GitHub Actions prima del
    # deploy, ma qui un problema blocca la pubblicazione PRIMA del push.
    with ui.fase("Costruzione del sito (MkDocs)"):
        ui.esegui([sys.executable, "-m", "mkdocs", "build", "--quiet"], env=ENV_MKDOCS)
    with ui.fase("Controllo del sito") as stato:
        uscita = ui.esegui([sys.executable, str(SCRIPTS_DIR / "controlla_sito.py"),
                            str(ROOT_DIR / "site")])
        m = re.search(r"Link interni: (\d+) controllati in (\d+) pagine", uscita)
        if m:
            stato["dettaglio"] = f"{m.group(2)} pagine · {m.group(1)} link"

    stampa_riepilogo_build(solo_se_presenti=True)


def interattivo():
    """True se c'è una persona davanti al terminale (doppio click, cmd...)."""
    try:
        return sys.stdin.isatty()
    except (AttributeError, ValueError):
        return False


def _stile_stato(riga):
    codice = riga[:2]
    if "D" in codice:
        return "errore"
    if "?" in codice or "A" in codice:
        return "ok"
    return "avviso"


def conferma_pubblicazione(titolo, corpo, chiedi_conferma=True):
    """Mostra cosa sta per essere pubblicato e, se richiesto, chiede conferma.

    Senza terminale interattivo (es. lancio da un altro programma) o con
    --si non chiede nulla e prosegue, come faceva il Launcher prima.
    """
    righe = [f"[titolo]{ui.esc(titolo)}[/]"]
    righe += [f"[tenue]{ui.esc(r)}[/]" for r in (corpo.splitlines() if corpo else [])]
    modificati = git_stato(percorsi_esistenti()) + file_preparati_fuori_percorsi()
    righe += ["", f"{len(modificati)} file modificati:"]
    for r in modificati[:15]:
        righe.append(f"  [{_stile_stato(r)}]{ui.esc(r[:2])}[/] {ui.esc(r[3:])}")
    if len(modificati) > 15:
        righe.append(f"  [tenue]… e altri {len(modificati) - 15}[/]")
    esclusi = file_esclusi()
    if esclusi:
        righe += ["", f"[avviso]{len(esclusi)} file fuori dai percorsi pubblicati "
                      "(NON verranno inviati):[/]"]
        righe += [f"  [tenue]{ui.esc(r)}[/]" for r in esclusi[:8]]
    avvisi = sum(v["gravita"] == esito.AVVISO for v in esito.leggi_riepilogo())
    if avvisi:
        righe += ["", f"[avviso]La generazione ha prodotto {_conta(avvisi, 'avviso', 'avvisi')} "
                      "(vedi sopra).[/]"]
    ui.scrivi()
    ui.pannello("Cosa verrà pubblicato", righe)

    if not chiedi_conferma:
        return True
    if not interattivo():
        ui.scrivi("  (esecuzione non interattiva: pubblico senza chiedere conferma)", "tenue")
        return True
    # "\\[" : la parentesi quadra va protetta, altrimenti rich la legge come markup.
    risposta = ui.chiedi("  Pubblicare su GitHub? \\[s/N] ").lower()
    return risposta in ("s", "si", "sì", "y", "yes")


def pubblica(messaggio=None, chiedi_conferma=True):
    """Commit e push delle modifiche (dopo prepara() e genera_sito())."""
    if not git_ci_sono_modifiche():
        ui.scrivi()
        ui.pannello("Niente da pubblicare",
                    ["Il sito generato coincide con l'ultima versione pubblicata."], "grey50")
        return False

    messaggio_globale["testo"] = messaggio  # None -> messaggio automatico
    titolo, corpo = componi_messaggio_commit()
    if not conferma_pubblicazione(titolo, corpo, chiedi_conferma):
        ui.scrivi()
        ui.pannello("Pubblicazione annullata",
                    ["Niente è stato inviato a GitHub: le modifiche restano nella cartella,",
                     "pronte per la prossima pubblicazione."], "yellow")
        return False

    ui.scrivi()
    if not git_sync_pubblicazione(titolo, corpo):
        return False
    ui.scrivi()
    ui.pannello("Sito pubblicato",
                ["[ok]Le modifiche sono su GitHub.[/] GitHub Actions le metterà online",
                 "tra qualche minuto."], "green")
    return True


def aggiorna(messaggio=None, refresh_ia=None, only=None, skip_validation=False,
             chiedi_conferma=True):
    ui.intestazione("Pubblicazione del sito")
    inizio = time.monotonic()
    prepara(skip_validation=skip_validation)
    invalida_cache(only=only, refresh_ia=refresh_ia)
    genera_sito()
    ui.scrivi(f"  Sito generato e controllato in {time.monotonic() - inizio:.0f} s", "tenue")
    pubblica(messaggio, chiedi_conferma=chiedi_conferma)
    _chiusura()


def _chiusura():
    registro = ui.percorso_registro()
    if registro:
        ui.scrivi(f"  Registro completo: {registro}", "tenue")


def solo_validazione():
    """Controlla dati.xlsx e basta: nessuna generazione, nessuna pubblicazione."""
    ui.intestazione("Controllo dei dati")
    risultato = ui.cattura(run_validation, str(ROOT_DIR / "data"))
    if risultato.get("error"):
        raise ErroreComando(f"impossibile leggere i dati: {risultato['error']}")
    riepilogo = _riepilogo_validazione(risultato)
    if risultato.get("success"):
        ui.ok("Dati pronti per la pubblicazione", riepilogo)
    else:
        ui.fallito("Ci sono errori da correggere in dati.xlsx", riepilogo)
    _voci_validazione(risultato.get("voci", []), includi_note=True)
    return risultato.get("success", False)


def _porta_libera():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def anteprima(skip_validation=False):
    """Rigenera il sito e lo apre nel browser con `mkdocs serve`. Non pubblica."""
    ui.intestazione("Anteprima del sito")
    prepara(skip_validation=skip_validation, esporta=False)
    genera_sito()

    porta = _porta_libera()
    percorso = urlparse(SITE_URL).path.rstrip("/") + "/"
    indirizzo = f"http://127.0.0.1:{porta}{percorso}"
    ui.scrivi()
    ui.pannello("Anteprima in corso", [
        f"[titolo]{indirizzo}[/]",
        "Si aggiorna da sola se rigeneri il sito da un'altra finestra.",
        "[tenue]Ctrl+C per chiudere.[/]"], "green")
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
    ui.scrivi("  Anteprima chiusa.", "tenue")


def stampa_riepilogo_build(solo_se_presenti=False):
    """Riepilogo di errori e avvisi raccolti dagli script di generazione."""
    voci = esito.leggi_riepilogo()
    if not voci:
        if not solo_se_presenti:
            ui.scrivi("  Nessun errore e nessun avviso nell'ultima generazione.", "tenue")
        return
    righe = []
    for v in voci:
        stile = "errore" if v["gravita"] == esito.ERRORE else "avviso"
        righe.append(f"[{stile}]{v['gravita'].upper()}[/] [tenue]{ui.esc(v['fase'])}:[/] "
                     f"{ui.esc(v['messaggio'])}")
    errori = sum(v["gravita"] == esito.ERRORE for v in voci)
    ui.scrivi()
    ui.pannello(f"Errori e avvisi della generazione ({_conta(errori, 'errore', 'errori')}, "
                f"{_conta(len(voci) - errori, 'avviso', 'avvisi')})",
                righe, "red" if errori else "yellow")


def mostra_cache_stats():
    ui.intestazione("Statistiche della cache")
    CacheManager().print_stats()


def svuota_cache():
    ui.intestazione("Pulizia della cache")
    ui.cattura(CacheManager().clear_all)
    ui.ok("Cache completamente svuotata")


def mostra_errore(e, pubblicazione=True):
    righe = [ui.esc(e)]
    if pubblicazione:
        righe.append("[titolo]Il sito NON è stato pubblicato.[/]")
    registro = ui.percorso_registro()
    if registro:
        righe.append(f"[tenue]Registro completo: {registro}[/]")
    ui.scrivi()
    ui.pannello("Errore", righe, "red")


# ---------------------------------------------------------------------------
# Menu (doppio click sul Launcher)
# ---------------------------------------------------------------------------

VOCI_MENU = [
    ("1", "Controlla i dati", "dati.xlsx · non genera, non pubblica"),
    ("2", "Anteprima nel browser", "rigenera · non pubblica"),
    ("3", "Pubblica", "rigenera · mostra le modifiche · chiede conferma"),
    ("4", "Rigenera schede e pubblica", "es. AMI-0034"),
    ("5", "Riepilogo dell'ultima generazione", "errori e avvisi"),
    ("0", "Esci", ""),
]


def chiedi_id_schede():
    testo = ui.chiedi("  ID delle schede da rigenerare (es. AMI-0034, AMI-0035): ")
    ids = [i.strip().upper() for i in re.split(r"[,;\s]+", testo) if i.strip()]
    errati = [i for i in ids if not re.fullmatch(r"AMI-\d{4,}", i)]
    if errati:
        ui.avviso(f"ID non validi: {', '.join(errati)} (formato atteso: AMI-0034)")
        return None
    return ids or None


def mostra_menu():
    ui.intestazione()
    if ui.console:
        from rich.table import Table
        tabella = Table.grid(padding=(0, 2))
        tabella.add_column(justify="right", style="marchio")
        tabella.add_column(style="titolo")
        tabella.add_column(style="tenue")
        for tasto, voce, nota in VOCI_MENU:
            tabella.add_row(f"  {tasto}", voce, nota)
        ui.console.print(tabella)
    else:
        for tasto, voce, nota in VOCI_MENU:
            print(f"  {tasto}  {voce}" + (f"  ({nota})" if nota else ""))


def menu():
    while True:
        mostra_menu()
        try:
            scelta = (ui.console.input("\n  Scelta: ") if ui.console else input("\nScelta: ")).strip()
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
                ui.intestazione("Riepilogo dell'ultima generazione")
                stampa_riepilogo_build()
            else:
                ui.avviso("scelta non valida")
                continue
        except ErroreComando as e:
            mostra_errore(e, pubblicazione=scelta in ("3", "4"))
        except KeyboardInterrupt:
            ui.scrivi("\n  Interrotto: torno al menu.", "avviso")
        ui.chiedi("\n  Premi INVIO per tornare al menu…")


def main():
    global ui
    args = sys.argv[1:]
    if "--dettagli" in args:
        ui = Interfaccia(ROOT_DIR, verboso=True)
        args = [a for a in args if a != "--dettagli"]

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
        mostra_errore(e)
        codice_uscita = 1
    except KeyboardInterrupt:
        ui.scrivi("\n  Interrotto manualmente.", "avviso")
        codice_uscita = 1
    finally:
        if interattivo():
            ui.chiedi("\n  Premi INVIO per chiudere…")

    sys.exit(codice_uscita)


if __name__ == "__main__":
    main()
