import os
import re
import json
import glob
import shutil
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
from core.site_config import SITE_URL

# ========================================================================
# CONFIGURAZIONE GLOBALE
# ========================================================================
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'build')

# ========================================================================
# UTILITY FUNCTIONS
# ========================================================================

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

def pubblica_file_seo():
    print("\n[SEO] Pubblicazione file statici SEO in build/...")
    # 1. robots.txt: (ri)scritto sempre, con URL hardcoded
    robots_path = os.path.join(OUTPUT_DIR, 'robots.txt')
    robots_content = """# robots.txt — Archivio del Maoismo Italiano
User-agent: *
Allow: /
Sitemap: https://ami-aim.github.io/archivio-maoismo-italiano/sitemap.xml
Sitemap: https://ami-aim.github.io/archivio-maoismo-italiano/sitemap.txt
"""
    with open(robots_path, 'w', encoding='utf-8') as f:
        f.write(robots_content)
    print("   [OK] robots.txt scritto in build/")
    
    # Verifica che non ci siano file robots.txt in assets/ che potrebbero sovrascriverlo
    assets_robots = os.path.join(ROOT_DIR, 'assets', 'robots.txt')
    if os.path.exists(assets_robots):
        print(f"   [WARNING] Trovato {assets_robots} - verrà rimosso per evitare conflitti")
        os.remove(assets_robots)
    
    # 2. File di verifica Search Console (google*.html):
    #    copiati dalla root del repo (o da static/) dentro build/
    sorgenti = []
    sorgenti += glob.glob(os.path.join(ROOT_DIR, 'google*.html'))
    sorgenti += glob.glob(os.path.join(ROOT_DIR, 'static', 'google*.html'))
    if not sorgenti:
        print("   [INFO] Nessun file google*.html nella root: se devi verificare "
              "la Search Console, lascia il file di verifica nella root del repo "
              "e verrà copiato automaticamente.")
        return
    for src in sorgenti:
        dst = os.path.join(OUTPUT_DIR, os.path.basename(src))
        shutil.copyfile(src, dst)
        print(f"   [OK] Copiato {os.path.basename(src)} → build/")

def genera_sitemap(output_dir, df, persone, organizzazioni):
    """
    Genera sitemap.xml e sitemap.txt per SEO (Google, Bing, etc).
    Versione irrobustita:
     - Genera doppio formato (XML + TXT) per massima compatibilità
     - Verifica esistenza file prima di includerli (evita 404)
     - Escape XML corretto per caratteri speciali
     - lastmod W3C conforme
     - schemaLocation esplicito per validazione
    """
    print("\n[SITEMAP] Generazione della sitemap (XML + TXT)...")
    base_url = "https://ami-aim.github.io/archivio-maoismo-italiano"
    oggi_iso = datetime.now().strftime('%Y-%m-%d')
    
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
    
    # Pagine principali (verifica esistenza file)
    pagine = [
        {"loc": f"{base_url}/", "priority": "1.0", "changefreq": "weekly"},
    ]
    
    # Verifica esistenza progetto.md (potrebbe non esistere)
    progetto_path = os.path.join(output_dir, 'progetto.md')
    if os.path.exists(progetto_path):
        pagine.append({"loc": f"{base_url}/progetto/", "priority": "0.8", "changefreq": "monthly"})
    else:
        print("   [INFO] progetto.md non trovato, escluso dalla sitemap")
    
    # Pagine che esistono sempre (generate dagli script)
    pagine.extend([
        {"loc": f"{base_url}/documenti/", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{base_url}/persone/", "priority": "0.8", "changefreq": "monthly"},
        {"loc": f"{base_url}/organizzazioni/", "priority": "0.8", "changefreq": "monthly"},
    ])
    
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
    
    # ============================================================
    # GENERA sitemap.xml
    # ============================================================
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 '
        'http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">'
    ]
    for pagina in pagine:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{escape_xml(pagina["loc"])}</loc>')
        xml_lines.append(f'    <lastmod>{oggi_iso}</lastmod>')
        xml_lines.append(f'    <changefreq>{pagina["changefreq"]}</changefreq>')
        xml_lines.append(f'    <priority>{pagina["priority"]}</priority>')
        xml_lines.append('  </url>')
    xml_lines.append('</urlset>')
    
    sitemap_xml_path = os.path.join(output_dir, 'sitemap.xml')
    with open(sitemap_xml_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines))
    
    # ============================================================
    # GENERA sitemap.txt (formato text sitemap accettato da Google)
    # Un URL per riga, senza header, senza metadati
    # ============================================================
    txt_lines = [pagina["loc"] for pagina in pagine]
    sitemap_txt_path = os.path.join(output_dir, 'sitemap.txt')
    with open(sitemap_txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(txt_lines))
    
    # ============================================================
    # AUTO-VERIFICA
    # ============================================================
    # Verifica XML
    with open(sitemap_xml_path, 'r', encoding='utf-8') as f:
        primo_xml = f.read(5)
    if primo_xml == '<?xml':
        print(f"   [OK] sitemap.xml generata ({len(pagine)} URL)")
    else:
        print(f"   [WARN] sitemap.xml: primi caratteri inattesi: {primo_xml!r}")
    
    # Verifica TXT (prima riga deve essere un URL)
    with open(sitemap_txt_path, 'r', encoding='utf-8') as f:
        prima_riga = f.readline().strip()
    if prima_riga.startswith('http'):
        print(f"   [OK] sitemap.txt generata ({len(pagine)} URL)")
    else:
        print(f"   [WARN] sitemap.txt: prima riga inattesa: {prima_riga!r}")
    
    print(f"   [INFO] Entrambi i file pronti per essere serviti da GitHub Pages")

def ottimizza_json(output_dir):
    """
    Ottimizza JSON per frontend: solo minificazione (NO chunking).
    Tutti i documenti sono caricati subito in un unico file.
    
    Args:
        output_dir: Cartella output (docs/)
    """
    print("\n[OPTIMIZE] Ottimizzazione JSON per frontend (solo minificazione)...")
    documenti_json = os.path.join(output_dir, 'documenti.json')
    soggetti_json = os.path.join(output_dir, 'soggetti.json')
    
    # Minifica (riduzione 50-60%)
    if os.path.exists(documenti_json):
        JSONOptimizer.minify_json(documenti_json, documenti_json)
        print(f"   [OK] documenti.json minificato")
    
    if os.path.exists(soggetti_json):
        JSONOptimizer.minify_json(soggetti_json, soggetti_json)
        print(f"   [OK] soggetti.json minificato")
    
    #  RIMOSSO IL CHUNKING - tutti i documenti sono in un unico file

def stampa_statistiche(df, persone, organizzazioni, cache_mgr=None):
    """
    Stampa statistiche finali di generazione.
    
    Args:
        df: DataFrame catalogo
        persone: dict persone
        organizzazioni: dict organizzazioni
        cache_mgr: CacheManager opzionale
    """
    print("\n" + "=" * 60)
    print("STATISTICHE GENERAZIONE")
    print("=" * 60)
    print(f"Documenti: {len(df)}")
    print(f"Persone: {len(persone)}")
    print(f"Organizzazioni: {len(organizzazioni)}")
    if cache_mgr:
        cache_mgr.print_stats()
    print("=" * 60 + "\n")

# ========================================================================
# MAIN
# ========================================================================

def main():
    """
    Funzione principale: orchestrazione completa generazione.
    """
    print("=" * 60)
    print("GENERATORE AMI - ARCHIVIO MAOISMO ITALIANO")
    print("=" * 60)
    print(f"Inizio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
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
    if excel_changed:
        # Persone e organizzazioni influenzano anche i link delle schede: il
        # file Excel e' quindi l'unita' minima sicura di invalidazione.
        cache_mgr.clear_doc_metadata()
    
    # ================================================================
    # PREPARAZIONE: Immagini profilo + file SEO statici
    # ================================================================
    print("\n[PREP] Preparazione risorse...")
    copia_immagini_profili()
    pubblica_file_seo()
    
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
    print("=" * 60)
    print("GENERAZIONE COMPLETATA CON SUCCESSO!")
    print(f"Fine: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

# ========================================================================
# ENTRY POINT
# ========================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Generazione interrotta dall'utente.")
    except Exception as e:
        print(f"\n[FATAL] Errore fatale durante generazione:\n{e}")
        raise