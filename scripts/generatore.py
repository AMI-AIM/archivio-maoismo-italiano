import os
import shutil
import pandas as pd
from core.soggetti import carica_soggetti, genera_json_soggetti
from core.schede import crea_schede
from core.archivio import genera_indice
from core.json_export import genera_json
from core.home import genera_home

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'docs')
IMMAGINI_DIR = os.path.join(ROOT_DIR, 'immagini', 'profili')


def copia_immagini_profili():
    """Copia le immagini dei profili e il placeholder nella cartella docs."""
    src_dir = IMMAGINI_DIR
    dst_dir = os.path.join(OUTPUT_DIR, 'immagini', 'profili')
    
    if not os.path.exists(src_dir):
        print("   ⚠️ Cartella 'immagini/profili/' non trovata. Nessuna immagine copiata.")
        return
    
    os.makedirs(dst_dir, exist_ok=True)
    copiate = 0
    for file in os.listdir(src_dir):
        src_path = os.path.join(src_dir, file)
        dst_path = os.path.join(dst_dir, file)
        if os.path.isfile(src_path):
            shutil.copy2(src_path, dst_path)
            copiate += 1
    
    # 🔥 Se placeholder.png non esiste, crea un placeholder di base
    placeholder_path = os.path.join(dst_dir, 'placeholder.png')
    if not os.path.exists(placeholder_path):
        # Crea un placeholder PNG di base (100x100, grigio con testo "?")
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (100, 100), color='#888888')
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            draw.text((50, 50), "?", fill='white', anchor="mm", font=font)
            img.save(placeholder_path)
            print(f"   ✅ Creato placeholder.png in 'docs/immagini/profili/'")
        except ImportError:
            print("   ⚠️ Pillow non installato. Assicurati che placeholder.png esista nella cartella immagini/profili/")
        except Exception as e:
            print(f"   ⚠️ Impossibile creare placeholder.png: {e}")
    
    print(f"   ✅ Copiate {copiate} immagini profili in 'docs/immagini/profili/'")


def genera_sitemap(output_dir, df, persone, organizzazioni):
    """Genera un file sitemap.xml per i motori di ricerca."""
    print("\n🗺️ Generazione della sitemap...")
    
    base_url = "https://ami-aim.github.io/archivio-maoismo-italiano"
    
    def escape_xml(text):
        if not text:
            return ''
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
    
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
        slug = persone[nome]['slug']
        if slug:
            pagine.append({
                "loc": f"{base_url}/persone/{slug}/",
                "priority": "0.6",
                "changefreq": "monthly"
            })
    
    for nome in organizzazioni.keys():
        slug = organizzazioni[nome]['slug']
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
    
    sitemap_path = os.path.join(output_dir, 'sitemap.xml')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines))
    
    print(f"   ✅ Sitemap generata con {len(pagine)} pagine.")


def main():
    print("🚀 Avvio del generatore di schede AMI...")
    print(f"📂 Root: {ROOT_DIR}")
    print(f"📂 Dati: {DATA_DIR}")
    print(f"📂 Output: {OUTPUT_DIR}")
    
    # 🔥 COPIA IMMAGINI PROFILI
    copia_immagini_profili()
    
    persone, organizzazioni = carica_soggetti(DATA_DIR)
    genera_json_soggetti(persone, organizzazioni, OUTPUT_DIR)
    
    try:
        catalogo_path = os.path.join(DATA_DIR, 'catalogo.xlsx')
        df = pd.read_excel(catalogo_path, dtype=str).fillna('')
    except FileNotFoundError:
        print(f"❌ ERRORE: Non trovo '{catalogo_path}'.")
        return
    except Exception as e:
        print(f"❌ ERRORE durante la lettura di catalogo.xlsx: {e}")
        return
    
    df.columns = df.columns.str.strip().str.lower()
    print(f"📊 Trovate {len(df)} righe e le seguenti colonne: {list(df.columns)}")
    
    crea_schede(df, persone, organizzazioni, OUTPUT_DIR)
    genera_indice(df, OUTPUT_DIR)
    genera_json(df, persone, organizzazioni, OUTPUT_DIR)
    genera_home(df, persone, OUTPUT_DIR)
    genera_sitemap(OUTPUT_DIR, df, persone, organizzazioni)
    
    print("\n🎉 Conversione completata con successo!")


if __name__ == "__main__":
    main()