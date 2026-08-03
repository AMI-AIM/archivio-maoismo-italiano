import os
import re
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

from scripts.config import ROOT_DIR, DATA_DIR, BUILD_DIR
from scripts.core.soggetti import carica_soggetti, genera_json_soggetti
from scripts.core.schede import crea_schede
from scripts.core.archivio import genera_indice
from scripts.core.json_export import genera_json
from scripts.core.home import genera_home
from scripts.core.cache_manager import CacheManager
from scripts.core.json_optimizer import JSONOptimizer

def copia_immagini_profili():
    """
    Garantisce che placeholder.webp esista in build/immagini/profili/
    per avatar predefiniti di persone/organizzazioni senza foto.
    """
    dst_dir = BUILD_DIR / "immagini" / "profili"
    dst_dir.mkdir(parents=True, exist_ok=True)

    placeholder_path = dst_dir / "placeholder.webp"
    if not placeholder_path.exists():
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (100, 100), color='#888888')
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            draw.text((50, 50), "?", fill='white', anchor="mm", font=font)
            img.save(placeholder_path, 'WEBP')
            print(f"   [OK] Creato placeholder.webp in '{dst_dir}'")
        except ImportError:
            print("   [WARN] Pillow non installato. Usa placeholder.webp esistente.")
        except Exception as e:
            print(f"   [WARN] Impossibile creare placeholder.webp: {e}")
    else:
        print("   [OK] placeholder.webp gia presente")

def genera_sitemap(df, persone, organizzazioni):
    """
    Genera sitemap.xml per SEO.
    """
    print("\n[SITEMAP] Generazione della sitemap...")

    base_url = "https://ami-aim.github.io/archivio-maoismo-italiano"

    def escape_xml(text):
        if not text:
            return ''
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))

    pagine = [
        {"loc": f"{base_url}/", "priority": "1.0", "changefreq": "weekly"},
        {"loc": f"{base_url}/progetto/", "priority": "0.8", "changefreq": "monthly"},
        {"loc": f"{base_url}/documenti/", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{base_url}/persone/", "priority": "0.8", "changefreq": "monthly"},
        {"loc": f"{base_url}/organizzazioni/", "priority": "0.8", "changefreq": "monthly"},
    ]

    for _, row in df.iterrows():
        ami_id = str(row.get('id', '')).strip()
        if ami_id and ami_id not in ['nan', 'None']:
            pagine.append({
                "loc": f"{base_url}/documenti/{ami_id}/",
                "priority": "0.7",
                "changefreq": "monthly"
            })

    for nome in persone.keys():
        slug = persone[nome].get('slug', '')
        if slug:
            pagine.append({
                "loc": f"{base_url}/persone/{slug}/",
                "priority": "0.6",
                "changefreq": "monthly"
            })

    for nome in organizzazioni.keys():
        slug = organizzazioni[nome].get('slug', '')
        if slug:
            pagine.append({
                "loc": f"{base_url}/organizzazioni/{slug}/",
                "priority": "0.6",
                "changefreq": "monthly"
            })

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]

    for pagina in pagine:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{escape_xml(pagina["loc"])}</loc>')
        xml_lines.append(f'    <priority>{pagina["priority"]}</priority>')
        xml_lines.append(f'    <changefreq>{pagina["changefreq"]}</changefreq>')
        xml_lines.append('  </url>')

    xml_lines.append('</urlset>')

    sitemap_path = BUILD_DIR / 'sitemap.xml'
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines))

    print(f"   [OK] Sitemap generata con {len(pagine)} URL")

def ottimizza_json():
    """Ottimizza JSON per frontend."""
    print("\n[OPTIMIZE] Ottimizzazione JSON per frontend...")

    documenti_json = BUILD_DIR / "documenti.json"
    soggetti_json = BUILD_DIR / "soggetti.json"

    if documenti_json.exists():
        JSONOptimizer.minify_json(str(documenti_json), str(documenti_json))

    if soggetti_json.exists():
        JSONOptimizer.minify_json(str(soggetti_json), str(soggetti_json))

    if documenti_json.exists():
        try:
            JSONOptimizer.chunk_documents(str(documenti_json), chunk_size=50)
        except Exception as e:
            print(f"   [WARN] Chunking non riuscito: {e}")

def stampa_statistiche(df, persone, organizzazioni, cache_mgr=None):
    print("\n" + "="*60)
    print("STATISTICHE GENERAZIONE")
    print("="*60)
    print(f"Documenti: {len(df)}")
    print(f"Persone: {len(persone)}")
    print(f"Organizzazioni: {len(organizzazioni)}")

    if cache_mgr:
        cache_mgr.print_stats()

    print("="*60 + "\n")

def main():
    print("="*60)
    print("GENERATORE AMI - ARCHIVIO MAOISMO ITALIANO")
    print("="*60)
    print(f"Inizio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    print(f"\n[INFO] Root directory: {ROOT_DIR}")
    print(f"[INFO] Dati directory: {DATA_DIR}")
    print(f"[INFO] Build directory: {BUILD_DIR}")

    cache_mgr = CacheManager()
    catalogo_path = DATA_DIR / "dati.xlsx"

    print("\n[CACHE] Controllo cambiamenti file sorgente...")
    excel_changed = cache_mgr.is_file_changed(str(catalogo_path))

    print("\n[PREP] Preparazione risorse...")
    copia_immagini_profili()

    print("\n[LOAD] Caricamento persone e organizzazioni...")
    try:
        persone, organizzazioni = carica_soggetti(DATA_DIR)
        print(f"[OK] Caricate {len(persone)} persone e {len(organizzazioni)} organizzazioni")
    except Exception as e:
        print(f"[ERROR] Errore caricamento soggetti: {e}")
        return

    print("[EXPORT] Esportazione JSON soggetti...")
    genera_json_soggetti(persone, organizzazioni, BUILD_DIR)

    print("\n[LOAD] Caricamento catalogo documenti...")
    try:
        df = pd.read_excel(
            catalogo_path,
            sheet_name='Catalogo',
            dtype=str
        ).fillna('')
    except FileNotFoundError:
        print(f"[ERROR] File non trovato: {catalogo_path}")
        return
    except Exception as e:
        print(f"[ERROR] Errore lettura catalogo: {e}")
        return

    df.columns = df.columns.str.strip().str.lower()

    print(f"[OK] Caricate {len(df)} righe e {len(df.columns)} colonne")
    print(f"[INFO] Colonne: {', '.join(list(df.columns)[:5])}...")

    print("\n[GEN] Generazione schede documenti...")
    try:
        # CORREZIONE: rimuovi BUILD_DIR dalla chiamata
        conteggio_gen, conteggio_skip = crea_schede(
            df,
            persone,
            organizzazioni,
            cache_manager=cache_mgr
        )
        print(f"[OK] {conteggio_gen} generate, {conteggio_skip} saltate (cache)")
    except Exception as e:
        print(f"[ERROR] Errore generazione schede: {e}")
        raise

    print("\n[GEN] Generazione indice archivio...")
    try:
        genera_indice(df, BUILD_DIR)
        print(f"[OK] Indice archivio generato")
    except Exception as e:
        print(f"[ERROR] Errore generazione indice: {e}")
        raise

    print("\n[EXPORT] Esportazione JSON documenti...")
    try:
        genera_json(df, persone, organizzazioni, BUILD_DIR)
        print(f"[OK] JSON documenti esportato")
    except Exception as e:
        print(f"[ERROR] Errore esportazione JSON: {e}")
        raise

    print("\n[GEN] Generazione home page...")
    try:
        genera_home(df, persone, BUILD_DIR)
        print(f"[OK] Home page generata")
    except Exception as e:
        print(f"[ERROR] Errore generazione home: {e}")
        raise

    print("\n[SEO] Generazione sitemap...")
    try:
        genera_sitemap(df, persone, organizzazioni)
    except Exception as e:
        print(f"[WARN] Errore generazione sitemap: {e}")

    print("\n[OPTIMIZE] Ottimizzazione risorse frontend...")
    try:
        ottimizza_json()
    except Exception as e:
        print(f"[WARN] Errore ottimizzazione: {e}")

    print("\n[CACHE] Salvataggio state cache...")
    try:
        cache_mgr.set_file_hash(str(catalogo_path), cache_mgr._hash_file(str(catalogo_path)))
    except Exception as e:
        print(f"[WARN] Errore salvataggio cache: {e}")

    stampa_statistiche(df, persone, organizzazioni, cache_mgr)

    print("="*60)
    print("GENERAZIONE COMPLETATA CON SUCCESSO!")
    print(f"Fine: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Generazione interrotta dall'utente.")
    except Exception as e:
        print(f"\n[FATAL] Errore fatale durante generazione:\n{e}")
        raise