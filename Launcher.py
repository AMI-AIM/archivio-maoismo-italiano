"""
Launcher AMI — aggiorna e pubblica il sito.

Uso:
    python Launcher.py                          Rigenera e pubblica (con messaggio commit automatico)
    python Launcher.py "messaggio commit"       Rigenera e pubblica con messaggio custom
    python Launcher.py --refresh-ia ID1,ID2     Invalida la cache IA solo per gli identifier indicati,
                                                 poi rigenera e pubblica
    python Launcher.py --force-refresh-ia       Invalida TUTTA la cache IA (metadati + testi),
                                                 poi rigenera e pubblica
    python Launcher.py --clear-cache            Svuota tutta la cache (IA, hash file, metadati doc)
    python Launcher.py --cache-stats            Mostra statistiche cache
    python Launcher.py --help                   Mostra questo messaggio
"""

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

    requirements_path = ROOT_DIR / "requirements.txt"
    mappa_moduli = {
        "pandas": "pandas",
        "openpyxl": "openpyxl",
        "mkdocs-material": "mkdocs",
    }

    if requirements_path.exists():
        pacchetti = [
            riga.strip() for riga in requirements_path.read_text(encoding="utf-8").splitlines()
            if riga.strip() and not riga.strip().startswith("#")
        ]
    else:
        print(f"   ⚠️ '{requirements_path.name}' non trovato, uso elenco di fallback.")
        pacchetti = list(mappa_moduli.keys())

    for pacchetto in pacchetti:
        modulo = mappa_moduli.get(pacchetto, pacchetto.replace("-", "_"))
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
            msg += f"\n   Installa il resto con: pip install -r requirements.txt"
        raise ErroreComando(msg)

def git_ci_sono_modifiche():
    risultato = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT_DIR, capture_output=True, text=True
    )
    return bool(risultato.stdout.strip())


def aggiorna(messaggio=None, refresh_ia=None):
    stampa_titolo("🚀 Aggiornamento del sito AMI")

    verifica_dipendenze()

    # -1. Invalidazione mirata/globale cache IA, se richiesta
    if refresh_ia:
        stampa_titolo("♻️  Invalidazione cache Internet Archive")
        cache_mgr = CacheManager()
        if refresh_ia == 'all':
            cache_mgr.clear_ia_metadata()
            print("   Tutti i documenti verranno ri-scaricati da Internet Archive.")
        else:
            cache_mgr.clear_ia_metadata(refresh_ia)
            print(f"   Verranno ri-scaricati solo: {', '.join(refresh_ia)}")

    # 0. Sincronizzazione file statici (NUOVO — deve girare per primo)
    esegui([sys.executable, "sync_assets.py"], cwd=SCRIPTS_DIR,
           descrizione="🔄 Sincronizzazione file statici (assets/ → build/)")

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

    if not messaggio:
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
        # ✨ Gestisci opzioni CLI
        args = sys.argv[1:]
        refresh_ia = None
        messaggio = None

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

            if args and not args[0].startswith('--'):
                messaggio = args[0]

        aggiorna(messaggio=messaggio, refresh_ia=refresh_ia)
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