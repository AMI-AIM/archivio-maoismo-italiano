import os
import sys
from datetime import datetime

from core.archivio import genera_indice
from core.home import genera_home
from core.raccolta import inserisci_scheda_raccolta
from core import esito
from core.dati import leggi_foglio
from core.ead_export import esporta_tutto
from core.json_export import genera_json
from core.json_optimizer import JSONOptimizer
from core.schede import crea_schede

# Import moduli core
from core.site_config import data_pubblicazione
from core.soggetti import carica_soggetti, genera_json_soggetti
from core.utils import get_cache_manager

# ========================================================================
# CONFIGURAZIONE GLOBALE
# ========================================================================

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'build')


# ========================================================================
# UTILITY FUNCTIONS
# ========================================================================

def verifica_placeholder_profili():
    """
    Verifica che assets/immagini/profili/placeholder.webp esista nel repo.
    E' l'avatar predefinito delle schede persona/organizzazione senza foto:
    viene copiato in build/ da sync_assets.py (unica fonte: assets/, mai
    generato a runtime — vedi CONVENZIONI.md §6).
    """
    placeholder_src = os.path.join(ROOT_DIR, 'assets', 'immagini', 'profili', 'placeholder.webp')
    if os.path.exists(placeholder_src):
        print("[OK] placeholder.webp presente in 'assets/immagini/profili/'")
    else:
        esito.avviso(f"Manca {placeholder_src}: le schede senza foto avranno un avatar rotto.")


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
    print("[OK] robots.txt scritto in build/")

    # Verifica che non ci siano file robots.txt in assets/ che potrebbero sovrascriverlo
    assets_robots = os.path.join(ROOT_DIR, 'assets', 'robots.txt')
    if os.path.exists(assets_robots):
        esito.avviso(f"Trovato {assets_robots}: rimosso per evitare conflitti con robots.txt generato")
        os.remove(assets_robots)

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
    oggi_iso = data_pubblicazione().isoformat()

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
        print("[INFO] progetto.md non trovato, escluso dalla sitemap")

    # Pagine che esistono sempre (generate dagli script)
    pagine.extend([
        {"loc": f"{base_url}/documenti/", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{base_url}/galleria/", "priority": "0.7", "changefreq": "weekly"},
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
        # Solo le schede generate davvero da persone.py (chi non ha documenti
        # collegati non ha pagina: senza questo controllo la sitemap
        # elencava indirizzi inesistenti).
        if slug and os.path.isfile(os.path.join(output_dir, 'persone', f'{slug}.md')):
            pagine.append({
                "loc": f"{base_url}/persone/{slug}/",
                "priority": "0.6",
                "changefreq": "monthly"
            })

    # Aggiunge organizzazioni
    for nome in organizzazioni.keys():
        slug = organizzazioni[nome].get('slug', '')
        if slug and os.path.isfile(os.path.join(output_dir, 'organizzazioni', f'{slug}.md')):
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
        print(f"[OK] sitemap.xml generata ({len(pagine)} URL)")
    else:
        esito.avviso(f"sitemap.xml: primi caratteri inattesi: {primo_xml!r}")

    # Verifica TXT (prima riga deve essere un URL)
    with open(sitemap_txt_path, 'r', encoding='utf-8') as f:
        prima_riga = f.readline().strip()

    if prima_riga.startswith('http'):
        print(f"[OK] sitemap.txt generata ({len(pagine)} URL)")
    else:
        esito.avviso(f"sitemap.txt: prima riga inattesa: {prima_riga!r}")

    print("[INFO] Entrambi i file pronti per essere serviti da GitHub Pages")


def ottimizza_json(output_dir):
    """
    Ottimizza JSON per frontend: minificazione.

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
    # Usa singleton per garantire consistenza cache tra tutti i moduli
    cache_mgr = get_cache_manager()

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
    verifica_placeholder_profili()
    pubblica_file_seo()

    # ================================================================
    # CARICA SOGGETTI: Persone e organizzazioni
    # ================================================================
    print("\n[LOAD] Caricamento persone e organizzazioni...")
    # Un errore di lettura qui ferma lo script (codice 1): senza soggetti
    # il sito uscirebbe senza link a persone e organizzazioni.
    persone, organizzazioni = carica_soggetti(DATA_DIR)
    print(f"[OK] Caricate {len(persone)} persone e {len(organizzazioni)} organizzazioni")

    # Esporta JSON soggetti per ricerca
    print("[EXPORT] Esportazione JSON soggetti...")
    genera_json_soggetti(persone, organizzazioni, OUTPUT_DIR)

    # ================================================================
    # CARICA CATALOGO: Documenti
    # ================================================================
    print("\n[LOAD] Caricamento catalogo documenti...")
    df = leggi_foglio('Catalogo')
    # La colonna 'Percorsi' (percorsi tematici) e' letta internamente come
    # 'serie', chiave usata dal JSON e dai filtri (?serie=) del sito.
    if 'percorsi' in df.columns and 'serie' not in df.columns:
        df = df.rename(columns={'percorsi': 'serie'})

    print(f"[OK] Caricate {len(df)} righe e {len(df.columns)} colonne")
    print(f"[INFO] Colonne: {', '.join(list(df.columns)[:5])}...")

    # ================================================================
    # GENERAZIONE: Schede documenti
    # ================================================================
    print("\n[GEN] Generazione schede documenti...")
    # Fasi BLOCCANTI (esito.passo con bloccante=True): se falliscono il
    # sito sarebbe incompleto, quindi lo script termina con codice 1 e la
    # pubblicazione si ferma. Le fasi successive vengono comunque eseguite,
    # così il riepilogo mostra tutti i problemi in una volta.
    conteggi = esito.passo("Generazione schede documenti", crea_schede,
                           df, persone, organizzazioni, OUTPUT_DIR,
                           cache_manager=cache_mgr)
    if conteggi:
        print(f"[OK] {conteggi[0]} generate, {conteggi[1]} saltate (cache)")

    # ================================================================
    # GENERAZIONE: Indice archivio con filtri
    # ================================================================
    print("\n[GEN] Generazione indice archivio...")
    esito.passo("Generazione indice archivio", genera_indice,
                df, OUTPUT_DIR, cache_manager=cache_mgr)

    # ================================================================
    # EXPORT: JSON per ricerca e filtri frontend
    # ================================================================
    print("\n[EXPORT] Esportazione JSON documenti...")
    esito.passo("Esportazione JSON documenti (ricerca e filtri)", genera_json,
                df, persone, organizzazioni, OUTPUT_DIR)

    # ================================================================
    # EXPORT: EAD3 (documenti) ed EAC-CPF (record d'autorita')
    # ================================================================
    print("\n[EXPORT] Esportazione EAD3 / EAC-CPF...")
    # Fasi NON bloccanti: un problema diventa un avviso nel riepilogo.
    risultato_xml = esito.passo("Esportazione EAD3/EAC-CPF", esporta_tutto,
                                df, catalogo_path, OUTPUT_DIR, bloccante=False)
    if risultato_xml:
        n_file, errori = risultato_xml
        print(f"[OK] {n_file} file XML scritti in build/dati/")
        if errori is None:
            esito.avviso("EAD3/EAC-CPF non validati rispetto agli schemi: "
                         "installare lxml (pip install -r requirements.txt)")
        elif errori:
            dettaglio = "; ".join(f"{nome}: {msg[0]}" for nome, msg in list(errori.items())[:3])
            esito.avviso(f"{len(errori)} file XML non validi rispetto allo schema "
                         f"(primi: {dettaglio})")
        else:
            print("[OK] Tutti i file XML sono validi (ead3.xsd, eac.xsd)")

    # ================================================================
    # GENERAZIONE: Scheda ISAD(G) della raccolta (pagina Il progetto)
    # ================================================================
    print("\n[GEN] Scheda della raccolta (ISAD)...")
    inserita = esito.passo("Scheda della raccolta (ISAD)", inserisci_scheda_raccolta,
                           OUTPUT_DIR, catalogo_path, df, bloccante=False)
    if inserita:
        print("[OK] Scheda della raccolta inserita in progetto.md")
    elif inserita is not None:
        esito.avviso("Segnaposto della scheda raccolta non trovato in progetto.md: "
                     "la scheda ISAD(G) non compare nella pagina Il progetto")

    # ================================================================
    # GENERAZIONE: Home page
    # ================================================================
    print("\n[GEN] Generazione home page...")
    esito.passo("Generazione home page", genera_home,
                df, persone, OUTPUT_DIR, organizzazioni)

    # ================================================================
    # GENERAZIONE: Sitemap SEO
    # ================================================================
    print("\n[SEO] Generazione sitemap...")
    esito.passo("Generazione sitemap", genera_sitemap,
                OUTPUT_DIR, df, persone, organizzazioni, bloccante=False)

    # ================================================================
    # OTTIMIZZAZIONE: JSON compressione
    # ================================================================
    print("\n[OPTIMIZE] Ottimizzazione risorse frontend...")
    esito.passo("Ottimizzazione JSON", ottimizza_json, OUTPUT_DIR, bloccante=False)

    # ================================================================
    # SALVA HASH: Cache per prossima esecuzione
    # ================================================================
    print("\n[CACHE] Salvataggio state cache...")
    esito.passo("Salvataggio cache", lambda: cache_mgr.set_file_hash(
        catalogo_path, cache_mgr._hash_file(catalogo_path)), bloccante=False)

    # ================================================================
    # STATISTICHE FINALI
    # ================================================================
    stampa_statistiche(df, persone, organizzazioni, cache_mgr)

    print("=" * 60)
    print("GENERAZIONE NON RIUSCITA: vedi gli errori sopra" if esito.ci_sono_errori()
          else "GENERAZIONE COMPLETATA")
    print(f"Fine: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")


# ========================================================================
# ENTRY POINT
# ========================================================================

if __name__ == "__main__":
    sys.exit(esito.esegui_script("generatore", main))