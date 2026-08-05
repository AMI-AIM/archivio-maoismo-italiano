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
    print("\n🔄 Sincronizzazione file statici (assets/ → build/)...")

    if not os.path.isdir(ASSETS_DIR):
        print(f"   ⚠️ Cartella '{ASSETS_DIR}' non trovata: nessun file statico da copiare.")
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

    print(f"   ✅ Copiati {contatore} file statici in '{BUILD_DIR}'")


def main():
    sincronizza()


if __name__ == "__main__":
    main()