import subprocess
import sys
import shutil
from datetime import datetime
from pathlib import Path
from scripts.core.cache_manager import CacheManager

ROOT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT_DIR / "scripts"


class ErroreComando(Exception):
    pass


def stampa_titolo(testo):
    print()
    print("=" * 60)
    print(testo)
    print("=" * 60)


def esegui(comando, cwd=None, descrizione=None):
    """Esegue un comando, mostra l'output in tempo reale, interrompe la sequenza se fallisce."""
    if descrizione:
        stampa_titolo(descrizione)
    anteprima = ' '.join(f'"{c}"' if ' ' in c else c for c in comando)
    print(f"$ {anteprima}")
    risultato = subprocess.run(comando, cwd=cwd or ROOT_DIR)
    if risultato.returncode != 0:
        raise ErroreComando(
            f"il comando '{' '.join(comando)}' è fallito (codice {risultato.returncode})."
        )


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
        msg = f"mancano le dipendenze: {', '.join(mancanti)}."
        if "git" in mancanti:
            msg += "\n   Installa git dal sito ufficiale per il tuo sistema operativo."
        pacchetti_pip = [m for m in mancanti if m != "git"]
        if pacchetti_pip:
            msg += f"\n   Installa il resto con: pip install {' '.join(pacchetti_pip)}"
        raise ErroreComando(msg)


def git_ci_sono_modifiche():
    risultato = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT_DIR, capture_output=True, text=True
    )
    return bool(risultato.stdout.strip())


def aggiorna():
    stampa_titolo("🚀 Aggiornamento del sito AMI")

    verifica_dipendenze()

    # 1-3. Rigenerazione contenuti (ordine: persone/org PRIMA di generatore)
    esegui([sys.executable, "persone.py"], cwd=SCRIPTS_DIR,
           descrizione="👤 Generazione schede persone")
    esegui([sys.executable, "org.py"], cwd=SCRIPTS_DIR,
           descrizione="🏛️  Generazione schede organizzazioni")
    esegui([sys.executable, "generatore.py"], cwd=SCRIPTS_DIR,
           descrizione="📑 Generazione documenti, archivio, home, sitemap")

    # 4. Pubblicazione
    stampa_titolo("📤 Pubblicazione")

    if not git_ci_sono_modifiche():
        print("   ℹ️  Nessuna modifica rispetto all'ultimo commit: niente da pubblicare.")
        stampa_titolo("✅ Completato (nessuna modifica)")
        return

    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        messaggio = sys.argv[1]
    else:
        messaggio = f"Aggiornamento automatico del sito — {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    esegui(["git", "add", "-A"], descrizione="Git add")
    esegui(["git", "commit", "-m", messaggio], descrizione="Git commit")
    esegui(["git", "push"], descrizione="Git push")

    stampa_titolo("🎉 Sito aggiornato e pubblicato!")
    print("   GitHub Actions builderà e pubblicherà automaticamente su GitHub Pages")
    print("   (di solito ci vuole qualche minuto prima che sia visibile online).")


def mostra_cache_stats():
    """Mostra statistiche cache."""
    stampa_titolo("📊 Statistiche Cache")
    cache_mgr = CacheManager()
    cache_mgr.print_stats()


def svuota_cache():
    """Svuota cache."""
    stampa_titolo("🗑️ Pulizia Cache")
    cache_mgr = CacheManager()
    cache_mgr.clear_all()
    print("   ✅ Cache completamente svuotato")


def main():
    codice_uscita = 0
    try:
        # ✨ NUOVO: Gestisci opzioni CLI
        if len(sys.argv) > 1:
            if sys.argv[1] == '--clear-cache':
                svuota_cache()
                return
            elif sys.argv[1] == '--cache-stats':
                mostra_cache_stats()
                return
            elif sys.argv[1] == '--help':
                print(__doc__)
                return
        
        aggiorna()
    except ErroreComando as e:
        print(f"\n❌ ERRORE: {e}")
        print("   Il sito NON è stato pubblicato: correggi l'errore sopra e rilancia lo script.")
        codice_uscita = 1
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrotto manualmente.")
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