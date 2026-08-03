#!/usr/bin/env python3
import shutil
from pathlib import Path
from scripts.config import ASSETS_DIR, BUILD_DIR

def copy_assets():
    """Copia tutti gli asset statici da assets/ a build/."""
    if not ASSETS_DIR.exists():
        print(f"❌ Cartella asset non trovata: {ASSETS_DIR}")
        return False

    # Crea la cartella build se non esiste
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    # Copia l'intera struttura di assets in build
    for item in ASSETS_DIR.iterdir():
        dst = BUILD_DIR / item.name
        if item.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)

    print(f"✅ Asset copiati da {ASSETS_DIR} a {BUILD_DIR}")
    return True

if __name__ == "__main__":
    copy_assets()