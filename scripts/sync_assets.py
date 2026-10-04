import os
import shutil

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(ROOT_DIR, 'assets')
BUILD_DIR = os.path.join(ROOT_DIR, 'build')


def sincronizza():
    """Copia i file statici da assets/ dentro build/, sovrascrivendo
    eventuali versioni precedenti. Va eseguito PRIMA degli script di
    generazione (persone.py, org.py, generatore.py), che scrivono il
    resto dei contenuti direttamente in build/."""
    print("\nSincronizzazione file statici (assets/ → build/)...")

    if not os.path.isdir(ASSETS_DIR):
        print(f"Cartella '{ASSETS_DIR}' non trovata: nessun file statico da copiare.")
        return

    os.makedirs(BUILD_DIR, exist_ok=True)

    contatore = 0
    for radice, _, files in os.walk(ASSETS_DIR):
        for nome_file in files:
            sorgente = os.path.join(radice, nome_file)
            percorso_relativo = os.path.relpath(sorgente, ASSETS_DIR)
            destinazione = os.path.join(BUILD_DIR, percorso_relativo)
            os.makedirs(os.path.dirname(destinazione), exist_ok=True)
            shutil.copy2(sorgente, destinazione)
            contatore += 1

    print(f"Copiati {contatore} file statici in '{BUILD_DIR}'")

    # Guardia sui CSS delle pagine migrate (home, archivio, argomenti) e
    # sul foglio dei font self-hosted: dalla migrazione CSS sono asset
    # statici versionati in assets/, NON piu' blocchi <style> inline nel
    # markdown. Se mancano, la pagina sarebbe senza layout (o con il FOUT):
    # si fallisce in modo esplicito invece di pubblicare una home scarna.
    stili_build = os.path.join(BUILD_DIR, 'stylesheets')
    for sottocartella, nomi in (('stylesheets', ('home.css', 'archivio.css',
                                                 'argomenti.css', 'fonts.css')),
                                ('fonts', None)):
        cartella_dest = os.path.join(BUILD_DIR, sottocartella)
        cartella_src = os.path.join(ASSETS_DIR, sottocartella)
        if nomi is None:
            # woff2 dei font: copia mirata + guardia su esistenza
            dest_dir = cartella_dest
            os.makedirs(dest_dir, exist_ok=True)
            if not os.path.isdir(cartella_src):
                raise FileNotFoundError(
                    "assets/fonts/ mancante: i font self-hosted sono un "
                    "asset versionato, ripristinarlo dal repository")
            for fn in os.listdir(cartella_src):
                if fn.endswith('.woff2'):
                    shutil.copy2(os.path.join(cartella_src, fn),
                                 os.path.join(dest_dir, fn))
            n_font = len([f for f in os.listdir(dest_dir) if f.endswith('.woff2')])
            if n_font == 0:
                raise FileNotFoundError("nessun .woff2 copiato in build/fonts/")
            print(f"Font self-hosted sincronizzati ({n_font} file woff2)")
            continue
        for nome in nomi:
            dest = os.path.join(stili_build, nome)
            if os.path.exists(dest):
                continue
            fonte = os.path.join(cartella_src, nome)
            if os.path.exists(fonte):
                os.makedirs(stili_build, exist_ok=True)
                shutil.copy2(fonte, dest)
                print(f"Ripristinato {nome} mancante in build/ (fonte: assets/)")
            else:
                raise FileNotFoundError(
                    f"{nome} mancante sia in build/ sia in assets/{sottocartella}/: "
                    "ripristinarlo dal repository (e' un asset versionato)")


def main():
    sincronizza()


if __name__ == "__main__":
    import sys
    from core import esito
    sys.exit(esito.esegui_script("sync_assets", main))