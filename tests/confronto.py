"""
Confronto del sito generato con un riferimento ("golden test").

Genera il sito a partire da tests/dati_prova.xlsx (un piccolo estratto fisso
del catalogo, senza collegamenti a Internet Archive) in una cartella
temporanea, e confronta i file prodotti in build/ (pagine .md, JSON, XML,
sitemap) con quelli salvati in tests/riferimento/.

- Nessuna differenza: le modifiche al codice non hanno cambiato il sito.
- Differenze: vengono elencate. Se sono volute (es. hai cambiato il modo in
  cui una scheda mostra le date) si accetta il nuovo risultato come
  riferimento; se non lo sono, hai trovato un effetto collaterale.

Uso:
    python -m tests.confronto              confronta (codice 1 se ci sono differenze)
    python -m tests.confronto --aggiorna   salva il risultato attuale come riferimento
Dal Launcher: voce "Test automatici" del menu.

I file copiati tali e quali da assets/ (CSS, JS, font, immagini) non vengono
confrontati: cambiano spesso per il design e non dipendono dal codice Python.
"""

import difflib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATI_PROVA = ROOT / "tests" / "dati_prova.xlsx"
RIFERIMENTO = ROOT / "tests" / "riferimento"
ESTENSIONI = {".md", ".json", ".xml", ".txt"}
DA_COPIARE = ["scripts", "assets", "overrides", "mkdocs.yml"]
SCRIPT = ["sync_assets.py", "persone.py", "org.py", "generatore.py", "argomenti.py", "galleria.py"]
# Data fissa (2 ottobre 2026) e ordine fisso: il risultato non cambia da un giorno all'altro.
AMBIENTE = {"SOURCE_DATE_EPOCH": "1790899200", "PYTHONHASHSEED": "0",
            "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}


class GenerazioneFallita(Exception):
    pass


def genera(cartella):
    """Copia il progetto in `cartella`, mette dati_prova.xlsx al posto dei dati e genera."""
    cartella = Path(cartella)
    for nome in DA_COPIARE:
        sorgente = ROOT / nome
        if sorgente.is_dir():
            shutil.copytree(sorgente, cartella / nome,
                            ignore=shutil.ignore_patterns("__pycache__", ".cache"))
        else:
            shutil.copy2(sorgente, cartella / nome)
    (cartella / "data").mkdir()
    shutil.copy2(DATI_PROVA, cartella / "data" / "dati.xlsx")
    ambiente = {**os.environ, **AMBIENTE}
    for script in SCRIPT:
        r = subprocess.run([sys.executable, script], cwd=cartella / "scripts", env=ambiente,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            uscita = r.stdout.decode("utf-8", errors="replace")
            raise GenerazioneFallita(f"{script} è fallito:\n" + "\n".join(uscita.splitlines()[-20:]))
    return cartella / "build"


def leggi(build):
    """{percorso relativo: testo} dei file confrontabili."""
    file = {}
    for percorso in sorted(Path(build).rglob("*")):
        if percorso.is_file() and percorso.suffix in ESTENSIONI:
            rel = percorso.relative_to(build).as_posix()
            sorgente_assets = ROOT / "assets" / rel
            testo = percorso.read_text(encoding="utf-8")
            # Copiato tale e quale da assets/: non è prodotto dal codice.
            if sorgente_assets.is_file() and sorgente_assets.read_text(encoding="utf-8") == testo:
                continue
            file[rel] = testo
    return file


def confronta():
    """Restituisce (aggiunti, rimossi, cambiati, {file: diff}) rispetto al riferimento."""
    with tempfile.TemporaryDirectory(prefix="ami-test-") as tmp:
        attuali = leggi(genera(tmp))
    riferimento = leggi(RIFERIMENTO) if RIFERIMENTO.is_dir() else {}
    aggiunti = sorted(set(attuali) - set(riferimento))
    rimossi = sorted(set(riferimento) - set(attuali))
    cambiati = sorted(f for f in set(attuali) & set(riferimento) if attuali[f] != riferimento[f])
    differenze = {}
    for f in cambiati:
        righe = difflib.unified_diff(riferimento[f].splitlines(), attuali[f].splitlines(),
                                     "riferimento", "attuale", n=0, lineterm="")
        differenze[f] = [r for r in righe if not r.startswith(("---", "+++"))]
    return aggiunti, rimossi, cambiati, differenze


def aggiorna_riferimento():
    with tempfile.TemporaryDirectory(prefix="ami-test-") as tmp:
        attuali = leggi(genera(tmp))
    if RIFERIMENTO.exists():
        shutil.rmtree(RIFERIMENTO)
    for rel, testo in attuali.items():
        destinazione = RIFERIMENTO / rel
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        destinazione.write_text(testo, encoding="utf-8", newline="")
    return len(attuali)


def main():
    if "--aggiorna" in sys.argv[1:]:
        n = aggiorna_riferimento()
        print(f"Riferimento aggiornato: {n} file in tests/riferimento/")
        return 0
    aggiunti, rimossi, cambiati, differenze = confronta()
    if not (aggiunti or rimossi or cambiati):
        print("Nessuna differenza: il sito di prova è identico al riferimento.")
        return 0
    for titolo, elenco in (("Nuovi", aggiunti), ("Spariti", rimossi), ("Cambiati", cambiati)):
        for f in elenco:
            print(f"{titolo}: {f}")
    for f, righe in differenze.items():
        print(f"\n--- {f}")
        for r in righe[:12]:
            print(r[:200])
        if len(righe) > 12:
            print(f"... altre {len(righe) - 12} righe")
    print("\nSe le differenze sono volute: python -m tests.confronto --aggiorna")
    return 1


if __name__ == "__main__":
    sys.exit(main())
