import os
import json
import html
import hashlib
from datetime import datetime

import pandas as pd

from core.utils import slugify, formatta_data
from core.site_config import site_path
from core.argomenti import build_argomenti_index, normalize_key, split_argomenti

try:
    from core.site_config import SITE_URL
except Exception:
    SITE_URL = "https://ami-aim.github.io/archivio-maoismo-italiano/"


# ============================================================
# CONFIGURAZIONE
# ============================================================

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'build')
ARGOMENTI_DIR = os.path.join(OUTPUT_DIR, 'argomenti')

# Cartelle in cui cercare le immagini degli argomenti.
# Fonte primaria: assets/ (versionata). Fallback: build/ (gia' sincronizzata).
ASSETS_ARGOMENTI_IMG_DIR = os.path.join(ROOT_DIR, 'assets', 'immagini', 'argomenti')
BUILD_ARGOMENTI_IMG_DIR = os.path.join(OUTPUT_DIR, 'immagini', 'argomenti')
ESTENSIONI_IMMAGINE = ['.webp', '.jpg', '.jpeg', '.png']

BASE_URL = str(SITE_URL).rstrip('/')

RESERVED_SLUGS = {
    'index',
    '404',
    'sitemap',
    'robots',
}

# La pagina ora E' in navigazione: la rendiamo ricercabile e indicizzata.
ESCLUDI_DALLA_RICERCA = False
AGGIORNA_SITEMAP = True


# ============================================================
# UTILITY
# ============================================================

def yaml_string(value):
    """Ritorna una stringa YAML-safe (JSON double-quoted)."""
    return json.dumps(str(value), ensure_ascii=False)


def escape_html(value):
    """Escape HTML."""
    return html.escape(str(value), quote=True)


def xml_escape(value):
    """Escape XML."""
    value = str(value)
    value = value.replace('&', '&amp;')
    value = value.replace('<', '&lt;')
    value = value.replace('>', '&gt;')
    value = value.replace('"', '&quot;')
    value = value.replace("'", '&apos;')
    return value


def formatta_data_sicura(raw):
    """Wrapper sicuro attorno a formatta_data."""
    raw = str(raw).strip()
    if not raw or raw in ['nan', 'None']:
        return 'n.d.', (9999, 1, 1)
    try:
        return formatta_data(raw)
    except Exception:
        return raw, (9999, 1, 1)


def count_text(num):
    """Testo leggibile per il conteggio documenti."""
    if num == 1:
        return '1 documento'
    return f'{num} documenti'


def get_years_text(docs):
    """Arco cronologico dei documenti collegati a un argomento."""
    years = set()
    for doc in docs:
        ordine = doc.get('data_ordine')
        if not isinstance(ordine, tuple) or not ordine:
            continue
        try:
            year = int(ordine[0])
        except (TypeError, ValueError):
            continue
        if year != 9999:
            years.add(year)
    if not years:
        return ''
    min_year = min(years)
    max_year = max(years)
    if min_year == max_year:
        return str(min_year)
    return f'{min_year}–{max_year}'


def find_column(df, candidates):
    """Trova la prima colonna disponibile tra quelle candidate."""
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def clean_argomenti_dir():
    """Rimuove i vecchi file Markdown generati nella cartella argomenti."""
    if not os.path.isdir(ARGOMENTI_DIR):
        return
    for filename in os.listdir(ARGOMENTI_DIR):
        if filename.endswith('.md'):
            try:
                os.remove(os.path.join(ARGOMENTI_DIR, filename))
            except OSError:
                pass


def make_slug(label, used_slugs):
    """Fallback locale per lo slug (usato solo se manca l'indice condiviso)."""
    base = slugify(label) or 'argomento'
    if base in RESERVED_SLUGS:
        base = 'argomento'
    slug = base
    counter = 2
    while slug in used_slugs or slug in RESERVED_SLUGS:
        slug = f'{base}-{counter}'
        counter += 1
    used_slugs.add(slug)
    return slug


# ============================================================
# IMMAGINI ARGOMENTI
# ============================================================

def colore_hash(nome):
    """Colore esadecimale stabile a partire dal nome (fallback senza foto)."""
    hash_obj = hashlib.md5(str(nome).encode('utf-8'))
    return f'#{hash_obj.hexdigest()[:6]}'


def scurisci(hex_color, fattore=0.55):
    """Scurisce un colore hex per il gradient di fallback."""
    hex_color = hex_color.lstrip('#')
    r = int(int(hex_color[0:2], 16) * fattore)
    g = int(int(hex_color[2:4], 16) * fattore)
    b = int(int(hex_color[4:6], 16) * fattore)
    return f'#{r:02x}{g:02x}{b:02x}'


def get_iniziali(nome, max_lettere=2):
    """Iniziali per la filigrana delle card senza foto."""
    parti = [p for p in str(nome).split() if p]
    if not parti:
        return '?'
    if len(parti) == 1:
        return parti[0][0].upper()
    return ''.join(p[0].upper() for p in parti[:max_lettere])


def trova_immagine_argomento(slug):
    """
    Cerca l'immagine di un argomento in assets/ e poi in build/.
    Ritorna (url, nome_file) oppure (None, None).
    """
    for base_dir in (ASSETS_ARGOMENTI_IMG_DIR, BUILD_ARGOMENTI_IMG_DIR):
        for est in ESTENSIONI_IMMAGINE:
            percorso = os.path.join(base_dir, f'{slug}{est}')
            if os.path.exists(percorso):
                return site_path(f'immagini/argomenti/{slug}{est}'), f'{slug}{est}'
    return None, None


# ============================================================
# GENERAZIONE SCHEDE SINGOLE
# ============================================================

def generate_single_page(item):
    """Genera la pagina singola di un argomento."""
    label = item['label']
    slug = item['slug']
    num_doc = item['num_doc']

    file_path = os.path.join(ARGOMENTI_DIR, f'{slug}.md')
    description = f"Documenti dell'Archivio del Maoismo Italiano collegati all'argomento {label}."

    css_url = site_path('stylesheets/soggetti.css')
    back_url = site_path('argomenti/')

    fm = []
    fm.append('---')
    fm.append(f'title: {yaml_string(label)}')
    fm.append(f'description: {yaml_string(description)}')
    fm.append('hide:')
    fm.append('  - navigation')
    fm.append('  - toc')
    fm.append('  - title')
    fm.append('---')
    fm.append('')

    body = []
    body.append(f'<link rel="stylesheet" href="{css_url}">')
    body.append('')
    body.append(f'<p style="margin: 0 0 1rem; font-size: 0.92rem;"><a href="{back_url}">← Tutti gli argomenti</a></p>')
    body.append(f'<h1 class="person-name">{escape_html(label)}</h1>')
    body.append(f'<div class="org-dates">{count_text(num_doc)}</div>')
    body.append('<p style="margin: 0.5rem 0 1rem 0; color: var(--md-default-fg-color--light);">')
    body.append('Documenti catalogati con questo argomento.')
    body.append('</p>')
    body.append('')
    body.append('<h2 style="font-weight: bold; font-size: 1.2rem; margin: 1.5rem 0 0.5rem 0;">Documenti</h2>')
    body.append('')
    body.append('<div class="catalogo-lista">')

    for doc in item['docs']:
        doc_url = site_path(f"documenti/{doc['id']}/")
        titolo_html = escape_html(doc['titolo'])
        data_html = escape_html(doc['data'])

        body.append('<div class="doc-row">')
        body.append(f'    <div class="doc-data">{data_html}</div>')
        body.append('    <div class="doc-contenuto">')
        body.append(f'        <div class="doc-titolo"><a href="{doc_url}">{titolo_html}</a></div>')

        if doc.get('badge'):
            badge_html = escape_html(doc['badge'])
            body.append(f'        <div class="doc-ruoli"><span class="ruolo-badge">{badge_html}</span></div>')

        body.append('    </div>')
        body.append('</div>')

    body.append('</div>')
    body.append('')

    content = '\n'.join(fm) + '\n' + '\n'.join(body)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'   ✅ Creata scheda argomento {label} → {slug}.md')


# ============================================================
# GENERAZIONE INDICE (HERO CARDS)
# ============================================================

def generate_index(argomenti):
    """
    Genera l'indice degli argomenti come elenco di hero card
    orizzontali a larghezza piena, con foto di sfondo e
    gradient solo nella parte bassa.
    """
    argomenti_ordinati = sorted(argomenti, key=lambda item: item['label'].lower())

    description_text = "Percorsi tematici dell'Archivio del Maoismo Italiano."

    lines = []

    lines.append('---')
    lines.append(f'title: {yaml_string("Percorsi tematici")}')
    lines.append(f'description: {yaml_string(description_text)}')
    lines.append('hide:')
    lines.append('  - navigation')
    lines.append('  - toc')
    lines.append('---')
    lines.append('')

    lines.append('<style>')
    lines.append('.hero-stack {')
    lines.append('    display: grid;')
    lines.append('    gap: 0.8rem;')
    lines.append('    margin: 0 0 2.5rem;')
    lines.append('}')
    lines.append('')
    lines.append('.hero-card {')
    lines.append('    position: relative;')
    lines.append('    display: block;')
    lines.append('    background: #141414;')
    lines.append('    width: 100%;')
    lines.append('    height: 480px;')
    lines.append('    border-radius: 0.8rem;')
    lines.append('    overflow: hidden;')
    lines.append('    text-decoration: none;')
    lines.append('    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.18);')
    lines.append('    transition: transform 180ms ease, box-shadow 180ms ease;')
    lines.append('}')
    lines.append('')
    lines.append('.hero-card:hover {')
    lines.append('    transform: translateY(-2px);')
    lines.append('    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28);')
    lines.append('    color: #ffffff;')
    lines.append('    text-decoration: none;')
    lines.append('}')
    lines.append('')
    lines.append('.hero-card:focus-visible {')
    lines.append('    outline: 3px solid var(--md-primary-fg-color);')
    lines.append('    outline-offset: 3px;')
    lines.append('}')
    lines.append('')
    lines.append('.hero-card-img {')
    lines.append('    position: absolute;')
    lines.append('    inset: 0;')
    lines.append('    width: 100%;')
    lines.append('    height: 100%;')
    lines.append('    object-fit: cover;')
    lines.append('    object-position: center center;')
    lines.append('    transition: transform 350ms ease;')
    lines.append('}')
    lines.append('')
    lines.append('.hero-card:hover .hero-card-img {')
    lines.append('    transform: scale(1.04);')
    lines.append('}')
    lines.append('')
    lines.append('.hero-card-iniziali {')
    lines.append('    position: absolute;')
    lines.append('    top: 0.8rem;')
    lines.append('    right: 1.2rem;')
    lines.append('    font-size: 5.5rem;')
    lines.append('    font-weight: 800;')
    lines.append('    color: rgba(255, 255, 255, 0.16);')
    lines.append('    line-height: 1;')
    lines.append('    user-select: none;')
    lines.append('}')
    lines.append('')
    lines.append('.hero-card-gradient {')
    lines.append('    position: absolute;')
    lines.append('    inset: 0;')
    lines.append('    background: linear-gradient(to top, rgba(0, 0, 0, 0.88) 0%, rgba(0, 0, 0, 0.45) 38%, rgba(0, 0, 0, 0) 68%);')
    lines.append('}')
    lines.append('')
    lines.append('.hero-card-content {')
    lines.append('    position: absolute;')
    lines.append('    left: 0;')
    lines.append('    right: 0;')
    lines.append('    bottom: 0;')
    lines.append('    padding: 1.1rem 1.4rem;')
    lines.append('    color: #ffffff;')
    lines.append('}')
    lines.append('')
    lines.append('.hero-card-nome {')
    lines.append('    font-size: 1.5rem;')
    lines.append('    font-weight: 700;')
    lines.append('    line-height: 1.25;')
    lines.append('    text-shadow: 0 1px 4px rgba(0, 0, 0, 0.55);')
    lines.append('    overflow-wrap: anywhere;')
    lines.append('}')
    lines.append('')
    lines.append('.hero-card-meta {')
    lines.append('    margin-top: 0.25rem;')
    lines.append('    font-size: 0.95rem;')
    lines.append('    color: rgba(255, 255, 255, 0.85);')
    lines.append('    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);')
    lines.append('}')
    lines.append('')
    lines.append('@media screen and (max-width: 40em) {')
    lines.append('    .hero-card {')
    lines.append('        height: 320px;')
    lines.append('        border-radius: 0.6rem;')
    lines.append('    }')
    lines.append('')
    lines.append('    .hero-card-nome {')
    lines.append('        font-size: 1.2rem;')
    lines.append('    }')
    lines.append('')
    lines.append('    .hero-card-content {')
    lines.append('        padding: 0.9rem 1.1rem;')
    lines.append('    }')
    lines.append('')
    lines.append('    .hero-card-iniziali {')
    lines.append('        font-size: 4rem;')
    lines.append('    }')
    lines.append('}')
    lines.append('</style>')
    lines.append('')

    lines.append('<div class="hero-stack">')

    for item in argomenti_ordinati:
        slug = item['slug']
        label_html = escape_html(item['label'])
        count = count_text(item['num_doc'])
        years = get_years_text(item['docs'])

        if years:
            meta = f'{count} · {years}'
        else:
            meta = count

        meta_html = escape_html(meta)

        if item.get('immagine'):
            lines.append(f'<a class="hero-card" href="{slug}/">')
            lines.append(f'    <img class="hero-card-img" src="{item["immagine"]}" alt="" loading="lazy">')
        else:
            colore = colore_hash(item['label'])
            scuro = scurisci(colore)
            iniziali = escape_html(get_iniziali(item['label']))
            lines.append(f'<a class="hero-card" href="{slug}/" style="background: linear-gradient(140deg, {colore} 0%, {scuro} 100%);">')
            lines.append(f'    <div class="hero-card-iniziali" aria-hidden="true">{iniziali}</div>')

        lines.append('    <div class="hero-card-gradient" aria-hidden="true"></div>')
        lines.append('    <div class="hero-card-content">')
        lines.append(f'        <div class="hero-card-nome">{label_html}</div>')
        lines.append(f'        <div class="hero-card-meta">{meta_html}</div>')
        lines.append('    </div>')
        lines.append('</a>')

    lines.append('</div>')
    lines.append('')

    index_path = os.path.join(ARGOMENTI_DIR, 'index.md')

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'   ✅ Indice argomenti generato come elenco di {len(argomenti)} hero card.')


# ============================================================
# SITEMAP
# ============================================================

def update_sitemap(argomenti):
    """
    Aggiunge le pagine argomento alla sitemap generata da generatore.py.
    Va eseguito DOPO generatore.py (ordine garantito da deploy.yml).
    """
    if not AGGIORNA_SITEMAP:
        return

    urls = [f'{BASE_URL}/argomenti/']
    for item in argomenti:
        urls.append(f"{BASE_URL}/argomenti/{item['slug']}/")

    oggi = datetime.now().strftime('%Y-%m-%d')

    xml_path = os.path.join(OUTPUT_DIR, 'sitemap.xml')

    if os.path.exists(xml_path):
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()

        blocks = []
        for url in urls:
            if url not in content:
                blocks.append(
                    '  <url>\n'
                    f'    <loc>{xml_escape(url)}</loc>\n'
                    f'    <lastmod>{oggi}</lastmod>\n'
                    '    <changefreq>monthly</changefreq>\n'
                    '    <priority>0.5</priority>\n'
                    '  </url>'
                )

        if blocks and '</urlset>' in content:
            content = content.replace(
                '</urlset>',
                '\n'.join(blocks) + '\n</urlset>'
            )
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'   ✅ sitemap.xml aggiornata con {len(blocks)} URL argomento.')
        else:
            print('   ℹ️ sitemap.xml già contiene le pagine argomento o non è modificabile.')
    else:
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        for url in urls:
            xml_lines.append('  <url>')
            xml_lines.append(f'    <loc>{xml_escape(url)}</loc>')
            xml_lines.append(f'    <lastmod>{oggi}</lastmod>')
            xml_lines.append('    <changefreq>monthly</changefreq>')
            xml_lines.append('    <priority>0.5</priority>')
            xml_lines.append('  </url>')
        xml_lines.append('</urlset>')
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(xml_lines))
        print(f'   ✅ sitemap.xml creata con {len(urls)} URL argomento.')

    txt_path = os.path.join(OUTPUT_DIR, 'sitemap.txt')
    existing_lines = set()
    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            existing_lines = set(line.strip() for line in f if line.strip())
        missing = [url for url in urls if url not in existing_lines]
        if missing:
            with open(txt_path, 'a', encoding='utf-8') as f:
                for url in missing:
                    f.write(url + '\n')
            print(f'   ✅ sitemap.txt aggiornata con {len(missing)} URL argomento.')
    else:
        with open(txt_path, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(url + '\n')
        print(f'   ✅ sitemap.txt creata con {len(urls)} URL argomento.')


# ============================================================
# MAIN
# ============================================================

def genera_argomenti():
    print('\n🏷️ Generazione delle pagine degli argomenti...')

    catalogo_path = os.path.join(DATA_DIR, 'dati.xlsx')

    try:
        df_catalogo = pd.read_excel(
            catalogo_path,
            sheet_name='Catalogo',
            dtype=str
        ).fillna('')
        df_catalogo.columns = df_catalogo.columns.str.strip().str.lower()
    except FileNotFoundError:
        print(f'   ❌ ERRORE: Non trovo {catalogo_path}.')
        return
    except Exception as e:
        print(f"   ❌ ERRORE durante la lettura del foglio 'Catalogo' in dati.xlsx: {e}")
        return

    if df_catalogo.empty:
        print("   ⚠️ Il foglio 'Catalogo' in dati.xlsx è vuoto.")
        return

    topic_column = find_column(
        df_catalogo,
        ['serie', 'argomenti', 'argomento', 'tag', 'tags']
    )

    if not topic_column:
        print("   ❌ ERRORE: nessuna colonna argomento trovata (cercavo 'Serie', 'Argomenti', 'Argomento', 'Tag', 'Tags').")
        return

    if 'id' not in df_catalogo.columns:
        print("   ❌ ERRORE: La colonna 'ID' non è presente nel foglio 'Catalogo'.")
        return

    print(f"   📊 Caricati {len(df_catalogo)} documenti dal foglio 'Catalogo' di dati.xlsx")
    print(f"   📊 Uso la colonna '{topic_column}' come fonte degli argomenti")

    os.makedirs(ARGOMENTI_DIR, exist_ok=True)
    clean_argomenti_dir()

    # ----------------------------------------------------------------
    # RACCOLTA DOCUMENTI PER ARGOMENTO
    # ----------------------------------------------------------------
    argomenti_map = {}

    for _, row in df_catalogo.iterrows():
        ami_id = str(row.get('id', '')).strip()
        if not ami_id or ami_id in ['nan', 'None']:
            continue

        titolo = str(row.get('titolo', '')).strip()
        if not titolo or titolo in ['nan', 'None']:
            titolo = 'Senza titolo'

        data_raw = str(row.get('data', '')).strip()
        if not data_raw or data_raw in ['nan', 'None']:
            data_raw = str(row.get('anno', '')).strip()

        data_form, data_ordine = formatta_data_sicura(data_raw)

        organizzazione = str(row.get('organizzazione', '')).strip()
        if organizzazione in ['nan', 'None']:
            organizzazione = ''
        tipo = str(row.get('tipo', '')).strip()
        if tipo in ['nan', 'None']:
            tipo = ''

        if organizzazione and tipo:
            badge = f'{organizzazione} · {tipo}'
        else:
            badge = organizzazione or tipo

        argomenti = split_argomenti(row.get(topic_column, ''))
        if not argomenti:
            continue

        doc = {
            'id': ami_id,
            'titolo': titolo,
            'data': data_form,
            'data_ordine': data_ordine,
            'badge': badge,
        }

        seen_keys = set()
        for argomento in argomenti:
            key = normalize_key(argomento)
            if not key or key in seen_keys:
                continue
            seen_keys.add(key)
            if key not in argomenti_map:
                argomenti_map[key] = [doc]
            else:
                argomenti_map[key].append(doc)

    if not argomenti_map:
        print('   ⚠️ Nessun argomento valido trovato.')
        return

    # ----------------------------------------------------------------
    # INDICE CONDIVISO: label + slug deterministici (coerenti con schede.py)
    # ----------------------------------------------------------------
    argomenti_index = build_argomenti_index(df_catalogo, topic_column)

    argomenti = []
    used_slugs_fallback = set()

    for key, docs in argomenti_map.items():
        index_entry = argomenti_index.get(key)
        if index_entry:
            label = index_entry['label']
            slug = index_entry['slug']
        else:
            label = key
            slug = make_slug(label, used_slugs_fallback)

        docs.sort(key=lambda d: (d['data_ordine'], d['titolo'].lower()))

        argomenti.append({
            'label': label,
            'slug': slug,
            'docs': docs,
            'num_doc': len(docs),
        })

    print(f'   📊 Trovati {len(argomenti)} argomenti con documenti associati.')

    # ----------------------------------------------------------------
    # IMMAGINI
    # ----------------------------------------------------------------
    for item in argomenti:
        immagine_url, immagine_file = trova_immagine_argomento(item['slug'])
        item['immagine'] = immagine_url
        item['immagine_file'] = immagine_file

    print('   🖼️  Stato immagini argomenti:')
    for item in sorted(argomenti, key=lambda x: x['label'].lower()):
        if item['immagine']:
            print(f"      ✅ {item['label']}: {item['immagine_file']}")
        else:
            print(f"      ⚠️  {item['label']}: nessuna immagine → fallback colorato.")
            print(f"          File atteso: assets/immagini/argomenti/{item['slug']}.webp (oppure .jpg/.jpeg/.png)")

    # ----------------------------------------------------------------
    # GENERAZIONE PAGINE
    # ----------------------------------------------------------------
    for item in argomenti:
        generate_single_page(item)

    generate_index(argomenti)

    update_sitemap(argomenti)

    print('   ✅ Generazione pagine argomenti completata.')


def main():
    print('🚀 Avvio del generatore di schede argomenti...')
    genera_argomenti()


if __name__ == '__main__':
    main()