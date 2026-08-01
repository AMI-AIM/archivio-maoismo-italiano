#!/usr/bin/env python3
"""
Aggiorna il sito AMI in un solo comando.

Esegue, nell'ordine:
  1. scripts/persone.py
  2. scripts/org.py
  3. scripts/generatore.py
  4. mkdocs build (controllo locale, non pubblica nulla da solo)
  5. git add / commit / push (pubblica su GitHub -> GitHub Actions fa il deploy)

Si ferma subito al primo errore, senza chiedere conferme in nessun altro caso.

Uso:
    python aggiorna_sito.py
    python aggiorna_sito.py "messaggio di commit personalizzato"
"""

import subprocess
import sys
import shutil
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT_DIR / "scripts"


def stampa_titolo(testo):
    print()
    print("=" * 60)
    print(testo)
    print("=" * 60)


def esegui(comando, cwd=None, descrizione=None):
    """Esegue un comando, mostra l'output in tempo reale, si ferma se fallisce."""
    if descrizione:
        stampa_titolo(descrizione)
    anteprima = ' '.join(f'"{c}"' if ' ' in c else c for c in comando)
    print(f"$ {anteprima}")
    risultato = subprocess.run(comando, cwd=cwd or ROOT_DIR)
    if risultato.returncode != 0:
        print(f"\n❌ ERRORE: il comando '{' '.join(comando)}' è fallito "
              f"(codice {risultato.returncode}).")
        print("   Il sito NON è stato pubblicato: correggi l'errore sopra e rilancia lo script.")
        sys.exit(1)


def verifica_dipendenze():
    stampa_titolo("🔎 Verifica dipendenze")
    mancanti = []
    for pacchetto, modulo in [("pandas", "pandas"), ("openpyxl", "openpyxl"),
                              ("mkdocs-material", "mkdocs")]:
        try:
            __import__(modulo)
            print(f"   ✅ {pacchetto}")
        except ImportError:
            print(f"   ❌ {pacchetto} non installato")
            mancanti.append(pacchetto)

    if not shutil.which("git"):
        print("   ❌ git non trovato nel PATH")
        mancanti.append("git")
    else:
        print("   ✅ git")

    if mancanti:
        print(f"\n❌ ERRORE: mancano le dipendenze: {', '.join(mancanti)}.")
        if "git" in mancanti:
            print("   Installa git dal sito ufficiale per il tuo sistema operativo.")
        pacchetti_pip = [m for m in mancanti if m != "git"]
        if pacchetti_pip:
            print(f"   Installa il resto con: pip install {' '.join(pacchetti_pip)}")
        sys.exit(1)


def git_ci_sono_modifiche():
    risultato = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT_DIR, capture_output=True, text=True
    )
    return bool(risultato.stdout.strip())


def main():
    stampa_titolo("🚀 Aggiornamento del sito AMI")

    verifica_dipendenze()

    # 1-3. Rigenerazione contenuti (ordine: persone/org PRIMA di generatore)
    esegui([sys.executable, "persone.py"], cwd=SCRIPTS_DIR,
           descrizione="👤 Generazione schede persone")
    esegui([sys.executable, "org.py"], cwd=SCRIPTS_DIR,
           descrizione="🏛️  Generazione schede organizzazioni")
    esegui([sys.executable, "generatore.py"], cwd=SCRIPTS_DIR,
           descrizione="📑 Generazione documenti, archivio, home, sitemap")

    # 4. Build locale di controllo (non pubblica nulla, serve solo a intercettare errori)
    esegui(["mkdocs", "build"], cwd=ROOT_DIR,
           descrizione="🔨 Build di controllo (mkdocs build)")

    # 5. Pubblicazione
    stampa_titolo("📤 Pubblicazione")

    if not git_ci_sono_modifiche():
        print("   ℹ️  Nessuna modifica rispetto all'ultimo commit: niente da pubblicare.")
        stampa_titolo("✅ Completato (nessuna modifica)")
        return

    if len(sys.argv) > 1:
        messaggio = sys.argv[1]
    else:
        messaggio = f"Aggiornamento automatico del sito — {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    esegui(["git", "add", "-A"], descrizione="Git add")
    esegui(["git", "commit", "-m", messaggio], descrizione="Git commit")
    esegui(["git", "push"], descrizione="Git push")

    stampa_titolo("🎉 Sito aggiornato e pubblicato!")
    print("   GitHub Actions builderà e pubblicherà automaticamente su GitHub Pages")
    print("   (di solito ci vuole qualche minuto prima che sia visibile online).")


if __name__ == "__main__":
    main()
