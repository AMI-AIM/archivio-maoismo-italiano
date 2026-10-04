"""
Esito della pipeline: errori bloccanti, avvisi e riepilogo finale.

Problema che risolve
--------------------
Prima, un errore in una fase della generazione (schede, home, indice...)
veniva stampato ma lo script terminava comunque con codice 0: il Launcher e
GitHub Actions credevano che tutto fosse andato bene e pubblicavano un sito
incompleto. Gli avvisi, invece, erano righe sparse nel terminale.

Regole
------
- ERRORE  = il sito pubblicato sarebbe rotto o incompleto (pagine mancanti,
  dati illeggibili). Lo script termina con codice 1 e la pubblicazione si
  ferma (Launcher) o il deploy fallisce (GitHub Actions).
- AVVISO  = qualcosa da sistemare che non rompe il sito (XML non valido
  rispetto allo schema, sitemap anomala, Internet Archive irraggiungibile,
  miniature non create...). La pubblicazione prosegue; l'avviso compare nel
  riepilogo finale.

Uso in uno script della pipeline:
    from core import esito
    ...
    if __name__ == '__main__':
        sys.exit(esito.esegui_script('persone', main))

Nei moduli:
    esito.avviso("testo")          # registra e stampa
    esito.errore("testo")          # registra e stampa; lo script uscirà con 1
    risultato = esito.passo("Generazione sitemap", genera_sitemap, ...,
                            bloccante=False)

Ogni script aggiunge le proprie voci a .riepilogo-build.json (nella radice
del progetto, escluso da Git); il Launcher lo azzera all'inizio e lo stampa
alla fine. Su GitHub Actions le voci finiscono anche nel riepilogo del run
(variabile GITHUB_STEP_SUMMARY), visibile nella pagina del workflow.
"""

import json
import os
import sys
import traceback
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
FILE_RIEPILOGO = ROOT_DIR / ".riepilogo-build.json"

ERRORE = "errore"
AVVISO = "avviso"

_stato = {"fase": None, "voci": []}


def inizia(fase):
    _stato["fase"] = fase
    _stato["voci"] = []


def _registra(gravita, messaggio):
    voce = {"fase": _stato["fase"] or "pipeline", "gravita": gravita, "messaggio": str(messaggio)}
    _stato["voci"].append(voce)
    etichetta = "ERRORE" if gravita == ERRORE else "AVVISO"
    print(f"[{etichetta}] {messaggio}")


def avviso(messaggio):
    _registra(AVVISO, messaggio)


def errore(messaggio):
    _registra(ERRORE, messaggio)


def ci_sono_errori():
    return any(v["gravita"] == ERRORE for v in _stato["voci"])


def passo(descrizione, funzione, *args, bloccante=True, **kwargs):
    """Esegue funzione(*args, **kwargs); un'eccezione diventa errore o avviso.

    Restituisce il risultato della funzione, oppure None se è fallita.
    """
    try:
        return funzione(*args, **kwargs)
    except Exception as e:
        testo = f"{descrizione}: {e.__class__.__name__}: {e}"
        if bloccante:
            errore(testo)
            traceback.print_exc()
        else:
            avviso(testo)
        return None


# ---------------------------------------------------------------------------
# Riepilogo condiviso tra gli script
# ---------------------------------------------------------------------------

def azzera_riepilogo():
    try:
        FILE_RIEPILOGO.unlink()
    except FileNotFoundError:
        pass


def leggi_riepilogo():
    try:
        return json.loads(FILE_RIEPILOGO.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return []


def _salva():
    if not _stato["voci"]:
        return
    voci = leggi_riepilogo() + _stato["voci"]
    try:
        FILE_RIEPILOGO.write_text(json.dumps(voci, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError as e:
        print(f"(impossibile scrivere {FILE_RIEPILOGO.name}: {e})")

    sommario = os.environ.get("GITHUB_STEP_SUMMARY")
    if sommario:
        righe = [f"### {_stato['fase']}"]
        for v in _stato["voci"]:
            righe.append(f"- **{v['gravita'].upper()}**: {v['messaggio']}")
        with open(sommario, "a", encoding="utf-8") as f:
            f.write("\n".join(righe) + "\n\n")


def formatta_riepilogo(voci):
    """Testo leggibile del riepilogo (usato dal Launcher)."""
    errori = [v for v in voci if v["gravita"] == ERRORE]
    avvisi = [v for v in voci if v["gravita"] == AVVISO]
    if not voci:
        return "Nessun errore, nessun avviso."
    righe = [f"{len(errori)} errori, {len(avvisi)} avvisi"]
    for titolo, gruppo in (("ERRORI (bloccano la pubblicazione)", errori),
                           ("AVVISI (da sistemare, non bloccano)", avvisi)):
        if gruppo:
            righe.append("")
            righe.append(titolo)
            for v in gruppo:
                righe.append(f"  - [{v['fase']}] {v['messaggio']}")
    return "\n".join(righe)


def concludi(codice=0):
    """Salva le voci e restituisce il codice d'uscita (1 se ci sono errori)."""
    if codice and not ci_sono_errori():
        errore("terminato con errore (vedi i messaggi sopra)")
    _salva()
    n_err = sum(v["gravita"] == ERRORE for v in _stato["voci"])
    n_avv = len(_stato["voci"]) - n_err
    if n_err or n_avv:
        print(f"\n[{_stato['fase']}] {n_err} errori, {n_avv} avvisi")
    return 1 if n_err else 0


def esegui_script(fase, main):
    """Punto d'ingresso standard: inizia, esegue main(), conclude.

    Un'eccezione non gestita o un main() che restituisce un valore diverso
    da 0/None diventano un ERRORE e il processo esce con codice 1.
    """
    inizia(fase)
    codice = 0
    try:
        risultato = main()
        # Attenzione: 1 == True in Python, quindi niente "in (None, 0, True)".
        riuscito = risultato is None or risultato is True or (
            type(risultato) is int and risultato == 0)
        codice = 0 if riuscito else 1
    except KeyboardInterrupt:
        print("\nInterrotto manualmente.")
        return 130
    except SystemExit as e:
        codice = 0 if e.code in (None, 0) else 1
    except Exception as e:
        if e.__class__.__name__ == "ErroreDati":
            # Problema nei dati (file o foglio mancante): messaggio chiaro,
            # senza traceback.
            errore(f"dati.xlsx: {e}")
        else:
            errore(f"errore imprevisto: {e.__class__.__name__}: {e}")
            traceback.print_exc()
        codice = 1
    return concludi(codice)


if __name__ == "__main__":
    # python -m scripts.core.esito -> stampa il riepilogo dell'ultima esecuzione
    print(formatta_riepilogo(leggi_riepilogo()))
    sys.exit(0)
