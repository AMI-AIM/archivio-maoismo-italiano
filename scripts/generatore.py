import os
import re
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import moduli core
from core.soggetti import carica_soggetti, genera_json_soggetti
from core.schede import crea_schede
from core.archivio import genera_indice
from core.json_export import genera_json
from core.home import genera_home
from core.cache_manager import CacheManager
from core.json_optimizer import JSONOptimizer


# ================================================================
# CONFIGURAZIONE GLOBALE
# ================================================================

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'docs')


# ================================================================
# UTILITY FUNCTIONS
# ================================================================

def copia_immagini_profili():
    """
    Garantisce che placeholder.webp esista in docs/immagini/profili/
    per avatar predefiniti di persone/organizzazioni senza foto.
    """
    dst_dir = os.path.join(OUTPUT_DIR, 'immagini', 'profili')
    os.makedirs(dst_dir, exist_ok=True)

    placeholder_path = os.path.join(dst_dir, 'placeholder.webp')
    if not os.path.exists(placeholder_path):
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
            print(f"   [OK] Creato placeholder.webp in 'docs/immagini/profili/'")
        except ImportError:
            print("   [WARN] Pillow non installato. Usa placeholder.webp esistente.")
        except Exception as e:
            print(f"   [WARN] Impossibile creare placeholder.webp: {e}")
    else:
        print("   [OK] placeholder.webp gia presente")


def genera_sitemap(output_dir, df, persone, organizzazioni):
    """
    Genera sitemap.xml per SEO (Google, Bing, etc).
    
    Args:
        output_dir: Cartella output (docs/)
        df: DataFrame catalogo
        persone: dict persone
        organizzazioni: dict organizzazioni
    """
    print("\n[SITEMAP] Generazione della sitemap...")
    
    base_url = "https://ami-aim.github.io/archivio-maoismo-italiano"
    
    def escape_xml(text):
        """Escape caratteri speciali per XML."""
        if not text:
            return ''
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))
    
    # Pagine principali
    pagine = [
        {"loc": f"{base_url}/", "priority": "1.0", "changefreq": "weekly"},
        {"loc": f"{base_url}/progetto/", "priority": "0.8", "changefreq": "monthly"},
        {"loc": f"{base_url}/documenti/", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{base_url}/persone/", "priority": "0.8", "changefreq": "monthly"},
        {"loc": f"{base_url}/organizzazioni/", "priority": "0.8", "changefreq": "monthly"},
    ]
    
    # Aggiunge documenti
    for _, row in df.iterrows():
        ami_id = str(row.get('id', '')).strip()
        if ami_id and ami_id not in ['nan', 'None']:
            pagine.append({
                "loc": f"{base_url}/documenti/{ami_id}/",
                "priority": "0.7",
                "changefreq": "monthly"
            })
    
    # Aggiunge persone
    for nome in persone.keys():
        slug = persone[nome].get('slug', '')
        if slug:
            pagine.append({
                "loc": f"{base_url}/persone/{slug}/",
                "priority": "0.6",
                "changefreq": "monthly"
            })
    
    # Aggiunge organizzazioni
    for nome in organizzazioni.keys():
        slug = organizzazioni[nome].get('slug', '')
        if slug:
            pagine.append({
                "loc": f"{base_url}/organizzazioni/{slug}/",
                "priority": "0.6",
                "changefreq": "monthly"
            })
    
    # Costruisce XML
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
    
    # Salva file
    sitemap_path = os.path.join(output_dir, 'sitemap.xml')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines))
    
    print(f"   [OK] Sitemap generata con {len(pagine)} URL")


def ottimizza_json(output_dir):
    """
    Ottimizza JSON per frontend: minificazione e chunking.
    
    Args:
        output_dir: Cartella output (docs/)
    """
    print("\n[OPTIMIZE] Ottimizzazione JSON per frontend...")
    
    documenti_json = os.path.join(output_dir, 'documenti.json')
    soggetti_json = os.path.join(output_dir, 'soggetti.json')
    
    # Minifica (riduzione 50-60%)
    if os.path.exists(documenti_json):
        JSONOptimizer.minify_json(documenti_json, documenti_json)
    
    if os.path.exists(soggetti_json):
        JSONOptimizer.minify_json(soggetti_json, soggetti_json)
    
    # Crea chunk per lazy loading archivio (opzionale)
    # Carica ~50 documenti alla volta
    if os.path.exists(documenti_json):
        try:
            JSONOptimizer.chunk_documents(documenti_json, chunk_size=50)
        except Exception as e:
            print(f"   [WARN] Chunking non riuscito: {e}")


def stampa_statistiche(df, persone, organizzazioni, cache_mgr=None):
    """
    Stampa statistiche finali di generazione.
    
    Args:
        df: DataFrame catalogo
        persone: dict persone
        organizzazioni: dict organizzazioni
        cache_mgr: CacheManager opzionale
    """
    print("\n" + "="*60)
    print("STATISTICHE GENERAZIONE")
    print("="*60)
    print(f"Documenti: {len(df)}")
    print(f"Persone: {len(persone)}")
    print(f"Organizzazioni: {len(organizzazioni)}")
    
    if cache_mgr:
        cache_mgr.print_stats()
    
    print("="*60 + "\n")


# ================================================================
# MAIN
# ================================================================

def main():
    """
    Funzione principale: orchestrazione completa generazione.
    """
    
    print("="*60)
    print("GENERATORE AMI - ARCHIVIO MAOISMO ITALIANO")
    print("="*60)
    print(f"Inizio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    print(f"\n[INFO] Root directory: {ROOT_DIR}")
    print(f"[INFO] Dati directory: {DATA_DIR}")
    print(f"[INFO] Output directory: {OUTPUT_DIR}")
    
    # ================================================================
    # CACHE MANAGER: Verifica cambiamenti file
    # ================================================================
    
    cache_mgr = CacheManager()
    catalogo_path = os.path.join(DATA_DIR, 'dati.xlsx')
    
    print("\n[CACHE] Controllo cambiamenti file sorgente...")
    excel_changed = cache_mgr.is_file_changed(catalogo_path)
    
    # ================================================================
    # PREPARAZIONE: Immagini profilo
    # ================================================================
    
    print("\n[PREP] Preparazione risorse...")
    copia_immagini_profili()
    
    # ================================================================
    # CARICA SOGGETTI: Persone e organizzazioni
    # ================================================================
    
    print("\n[LOAD] Caricamento persone e organizzazioni...")
    try:
        persone, organizzazioni = carica_soggetti(DATA_DIR)
        print(f"[OK] Caricate {len(persone)} persone e {len(organizzazioni)} organizzazioni")
    except Exception as e:
        print(f"[ERROR] Errore caricamento soggetti: {e}")
        return
    
    # Esporta JSON soggetti per ricerca
    print("[EXPORT] Esportazione JSON soggetti...")
    genera_json_soggetti(persone, organizzazioni, OUTPUT_DIR)
    
    # ================================================================
    # CARICA CATALOGO: Documenti
    # ================================================================
    
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
    
    # Normalizza colonne
    df.columns = df.columns.str.strip().str.lower()
    
    print(f"[OK] Caricate {len(df)} righe e {len(df.columns)} colonne")
    print(f"[INFO] Colonne: {', '.join(list(df.columns)[:5])}...")
    
    # ================================================================
    # GENERAZIONE: Schede documenti
    # ================================================================
    
    print("\n[GEN] Generazione schede documenti...")
    try:
        conteggio_gen, conteggio_skip = crea_schede(
            df,
            persone,
            organizzazioni,
            OUTPUT_DIR,
            cache_manager=cache_mgr
        )
        print(f"[OK] {conteggio_gen} generate, {conteggio_skip} saltate (cache)")
    except Exception as e:
        print(f"[ERROR] Errore generazione schede: {e}")
        raise
    
    # ================================================================
    # GENERAZIONE: Indice archivio con filtri
    # ================================================================
    
    print("\n[GEN] Generazione indice archivio...")
    try:
        genera_indice(df, OUTPUT_DIR)
        print(f"[OK] Indice archivio generato")
    except Exception as e:
        print(f"[ERROR] Errore generazione indice: {e}")
        raise
    
    # ================================================================
    # EXPORT: JSON per ricerca e filtri frontend
    # ================================================================
    
    print("\n[EXPORT] Esportazione JSON documenti...")
    try:
        genera_json(df, persone, organizzazioni, OUTPUT_DIR)
        print(f"[OK] JSON documenti esportato")
    except Exception as e:
        print(f"[ERROR] Errore esportazione JSON: {e}")
        raise
    
    # ================================================================
    # GENERAZIONE: Home page
    # ================================================================
    
    print("\n[GEN] Generazione home page...")
    try:
        genera_home(df, persone, OUTPUT_DIR)
        print(f"[OK] Home page generata")
    except Exception as e:
        print(f"[ERROR] Errore generazione home: {e}")
        raise
    
    # ================================================================
    # GENERAZIONE: Sitemap SEO
    # ================================================================
    
    print("\n[SEO] Generazione sitemap...")
    try:
        genera_sitemap(OUTPUT_DIR, df, persone, organizzazioni)
    except Exception as e:
        print(f"[WARN] Errore generazione sitemap: {e}")
    
    # ================================================================
    # OTTIMIZZAZIONE: JSON compressione
    # ================================================================
    
    print("\n[OPTIMIZE] Ottimizzazione risorse frontend...")
    try:
        ottimizza_json(OUTPUT_DIR)
    except Exception as e:
        print(f"[WARN] Errore ottimizzazione: {e}")
    
    # ================================================================
    # SALVA HASH: Cache per prossima esecuzione
    # ================================================================
    
    print("\n[CACHE] Salvataggio state cache...")
    try:
        cache_mgr.set_file_hash(catalogo_path, cache_mgr._hash_file(catalogo_path))
    except Exception as e:
        print(f"[WARN] Errore salvataggio cache: {e}")
    
    # ================================================================
    # STATISTICHE FINALI
    # ================================================================
    
    stampa_statistiche(df, persone, organizzazioni, cache_mgr)
    
    print("="*60)
    print("GENERAZIONE COMPLETATA CON SUCCESSO!")
    print(f"Fine: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Generazione interrotta dall'utente.")
    except Exception as e:
        print(f"\n[FATAL] Errore fatale durante generazione:\n{e}")
        raise