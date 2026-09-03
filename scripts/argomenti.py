import os
import re
import json
import html
import unicodedata
from datetime import datetime

import pandas as pd

from core.utils import slugify, formatta_data
from core.site_config import site_path

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

BASE_URL = str(SITE_URL).rstrip('/')

# Slug che non devono mai essere usati per una pagina argomento.
RESERVED_SLUGS = {
    'index',
    '404',
    'sitemap',
    'robots',
}

# Le pagine argomento devono restare fuori dalla navigazione.
# Con True, aggiunge frontmatter per escluderle dalla ricerca Material.
ESCLUDI_DALLA_RICERCA = True

# Con True, aggiunge le pagine argomento alla sitemap generata da generatore.py.
# Lascia False se vuoi pagine raggiungibili solo tramite URL diretto.
AGGIORNA_SITEMAP = False


# ============================================================
# UTILITY
# ============================================================

def yaml_string(value):
    """
    Restituisce una stringa YAML-safe usando JSON double-quoted string.
    """
    return json.dumps(str(value), ensure_ascii=False)


def escape_html(value):
    """
    Escape HTML.
    """
    return html.escape(str(value), quote=True)


def xml_escape(value):
    """
    Escape XML.
    """
    value = str(value)
    value = value.replace('&', '&amp;')
    value = value.replace('<', '&lt;')
    value = value.replace('>', '&gt;')
    value = value.replace('"', '&quot;')
    value = value.replace("'", '&apos;')
    return value


def normalize_key(value):
    """
    Normalizza il nome di un argomento per il raggruppamento.
    - minuscole;
    - rimozione accenti;
    - compressione spazi.
    """
    value = str(value).strip().lower()
    value = unicodedata.normalize('NFKD', value)
    value = ''.join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r'\s+', ' ', value)
    return value


def pulisci_valore(raw):
    """
    Pulisce un valore stringa proveniente dall'Excel.
    """
    txt = str(raw).strip()
    if txt.lower() in {'nan', 'none'}:
        return ''
    txt = re.sub(r'\s+', ' ', txt)
    return txt


def split_argomenti(raw):
    """
    Divide il contenuto del campo Serie/Argomenti.

    Nei dati attuali il separatore principale è ';'.
    Se non c'è ';', ma c'è ',', usa ',' come fallback.
    """
    txt = pulisci_valore(raw)
    if not txt:
        return []

    if ';' in txt or '\n' in txt:
        parti = re.split(r';|\n', txt)
    elif ',' in txt:
        parti = txt.split(',')
    else:
        parti = [txt]

    argomenti = []
    for parte in parti:
        parte = pulisci_valore(parte)
        if parte:
            argomenti.append(parte)

    return argomenti


def choose_label(current, new):
    """
    Scegli quale etichetta mostrare quando lo stesso argomento compare
    con differenze di maiuscole/minuscole.
    """
    if not current:
        return new

    if normalize_key(current) != normalize_key(new):
        return current

    current_upper = sum(1 for ch in current if ch.isupper())
    new_upper = sum(1 for ch in new if ch.isupper())

    if new_upper > current_upper:
        return new

    if current_upper == new_upper:
        if len(new) > len(current) and new != new.lower():
            return new

    return current


def formatta_data_sicura(raw):
    """
    Wrapper sicuro attorno a formatta_data.
    """
    raw = pulisci_valore(raw)

    if not raw:
        return 'n.d.', (9999, 1, 1)

    try:
        return formatta_data(raw)
    except Exception:
        return raw, (9999, 1, 1)


def make_slug(label, used_slugs):
    """
    Genera uno slug sicuro, evitando collisioni e slug riservati.
    """
    base = slugify(label)

    if not base or base in RESERVED_SLUGS:
        base = 'argomento'

    slug = base
    counter = 2

    while slug in used_slugs or slug in RESERVED_SLUGS:
        slug = f'{base}-{counter}'
        counter += 1

    used_slugs.add(slug)
    return slug


def count_text(num):
    """
    Testo leggibile per il conteggio documenti.
    """
    if num == 1:
        return '1 documento'
    return f'{num} documenti'


def get_years_text(docs):
    """
    Restituisce l'arco cronologico dei documenti collegati a un argomento.
    Esempio: '1967–1971' oppure '1968'.
    """
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
    """
    Trova la prima colonna disponibile tra quelle candidate.
    """
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def clean_argomenti_dir():
    """
    Rimuove i vecchi file Markdown generati nella cartella argomenti.
    Serve a evitare pagine residue quando un argomento viene eliminato.
    """
    if not os.path.isdir(ARGOMENTI_DIR):
        return

    for filename in os.listdir(ARGOMENTI_DIR):
        if filename.endswith('.md'):
            try:
                os.remove(os.path.join(ARGOMENTI_DIR, filename))
            except OSError:
                pass


# ============================================================
# GENERAZIONE SCHEDE SINGOLE
# ============================================================

def generate_single_page(item):
    """
    Genera la pagina singola di un argomento.
    """
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

    if ESCLUDI_DALLA_RICERCA:
        fm.append('search:')
        fm.append('  exclude: true')

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
# GENERAZIONE INDICE
# ============================================================

def generate_index(argomenti):
    """
    Genera un indice semplice degli argomenti come elenco di card
    orizzontali a larghezza piena.

    Nessuna sezione in evidenza, nessun filtro alfabetico.
    """
    # Ordine alfabetico.
    # Se preferisci ordinare per numero di documenti, usa:
    # argomenti_ordinati = sorted(argomenti, key=lambda item: (-item['num_doc'], item['label'].lower()))
    argomenti_ordinati = sorted(argomenti, key=lambda item: item['label'].lower())

    description_text = "Elenco degli argomenti presenti nell'Archivio del Maoismo Italiano."

    lines = []

    # ------------------------------------------------------------
    # FRONTMATTER
    # ------------------------------------------------------------

    lines.append('---')
    lines.append(f'title: {yaml_string("Argomenti")}')
    lines.append(f'description: {yaml_string(description_text)}')
    lines.append('hide:')
    lines.append('  - navigation')
    lines.append('  - toc')

    if ESCLUDI_DALLA_RICERCA:
        lines.append('search:')
        lines.append('  exclude: true')

    lines.append('---')
    lines.append('')

    # ------------------------------------------------------------
    # STILE DELLA PAGINA
    # ------------------------------------------------------------

    lines.append('<style>')
    lines.append('.argomenti-intro {')
    lines.append('    max-width: 70ch;')
    lines.append('    color: var(--md-default-fg-color--light);')
    lines.append('    margin: 0 0 1.25rem;')
    lines.append('}')
    lines.append('')
    lines.append('.argomenti-stack {')
    lines.append('    display: grid;')
    lines.append('    gap: 0.8rem;')
    lines.append('    margin: 0 0 2rem;')
    lines.append('}')
    lines.append('')
    lines.append('.argomento-card {')
    lines.append('    display: flex;')
    lines.append('    align-items: center;')
    lines.append('    justify-content: space-between;')
    lines.append('    gap: 1rem;')
    lines.append('    width: 100%;')
    lines.append('    min-height: 4.6rem;')
    lines.append('    padding: 1rem 1.2rem;')
    lines.append('    border: 1px solid rgba(0, 0, 0, 0.12);')
    lines.append('    border-left: 4px solid var(--md-primary-fg-color);')
    lines.append('    border-radius: 0.6rem;')
    lines.append('    background: var(--md-default-bg-color);')
    lines.append('    color: var(--md-default-fg-color);')
    lines.append('    text-decoration: none;')
    lines.append('    transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;')
    lines.append('}')
    lines.append('')
    lines.append('.argomento-card:hover {')
    lines.append('    transform: translateY(-1px);')
    lines.append('    box-shadow: 0 8px 22px rgba(0, 0, 0, 0.10);')
    lines.append('    color: var(--md-default-fg-color);')
    lines.append('    text-decoration: none;')
    lines.append('}')
    lines.append('')
    lines.append('.argomento-card:focus-visible {')
    lines.append('    outline: 3px solid var(--md-primary-fg-color);')
    lines.append('    outline-offset: 2px;')
    lines.append('}')
    lines.append('')
    lines.append('.argomento-card-main {')
    lines.append('    display: flex;')
    lines.append('    flex-direction: column;')
    lines.append('    gap: 0.25rem;')
    lines.append('    min-width: 0;')
    lines.append('}')
    lines.append('')
    lines.append('.argomento-card-nome {')
    lines.append('    font-size: 1.05rem;')
    lines.append('    font-weight: 600;')
    lines.append('    line-height: 1.35;')
    lines.append('    overflow-wrap: anywhere;')
    lines.append('}')
    lines.append('')
    lines.append('.argomento-card-meta {')
    lines.append('    color: var(--md-default-fg-color--light);')
    lines.append('    font-size: 0.92rem;')
    lines.append('}')
    lines.append('')
    lines.append('.argomento-card-freccia {')
    lines.append('    flex: 0 0 auto;')
    lines.append('    font-size: 1.25rem;')
    lines.append('    color: var(--md-primary-fg-color);')
    lines.append('}')
    lines.append('')
    lines.append('html[data-md-color-scheme="slate"] .argomento-card {')
    lines.append('    border-color: rgba(255, 255, 255, 0.16);')
    lines.append('}')
    lines.append('')
    lines.append('@media screen and (max-width: 40em) {')
    lines.append('    .argomento-card {')
    lines.append('        padding: 0.9rem 1rem;')
    lines.append('        min-height: 4.2rem;')
    lines.append('    }')
    lines.append('')
    lines.append('    .argomento-card-nome {')
    lines.append('        font-size: 1rem;')
    lines.append('    }')
    lines.append('}')
    lines.append('</style>')
    lines.append('')

    # ------------------------------------------------------------
    # CONTENUTO
    # ------------------------------------------------------------

    lines.append('<div class="argomenti-intro">')
    lines.append('Elenco dei percorsi tematici presenti in archivio. Ogni argomento raccoglie i documenti catalogati con quella serie.')
    lines.append('</div>')
    lines.append('')

    lines.append('<div class="argomenti-stack">')

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

        lines.append(f'<a class="argomento-card" href="{slug}/">')
        lines.append('    <span class="argomento-card-main">')
        lines.append(f'        <span class="argomento-card-nome">{label_html}</span>')
        lines.append(f'        <span class="argomento-card-meta">{meta_html}</span>')
        lines.append('    </span>')
        lines.append('    <span class="argomento-card-freccia" aria-hidden="true">→</span>')
        lines.append('</a>')

    lines.append('</div>')
    lines.append('')

    index_path = os.path.join(ARGOMENTI_DIR, 'index.md')

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'   ✅ Indice argomenti generato come elenco di {len(argomenti)} card.')


# ============================================================
# SITEMAP OPZIONALE
# ============================================================

def update_sitemap(argomenti):
    """
    Aggiunge le pagine argomento alla sitemap, se AGGIORNA_SITEMAP = True.

    Va eseguito dopo generatore.py, perché generatore.py crea
    build/sitemap.xml e build/sitemap.txt.
    """
    if not AGGIORNA_SITEMAP:
        return

    urls = [f'{BASE_URL}/argomenti/']

    for item in argomenti:
        urls.append(f"{BASE_URL}/argomenti/{item['slug']}/")

    oggi = datetime.now().strftime('%Y-%m-%d')

    # ------------------------------------------------------------
    # sitemap.xml
    # ------------------------------------------------------------

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
            print('   ℹ️ sitemap.xml già contiene tutte le pagine argomento o non è modificabile.')
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

    # ------------------------------------------------------------
    # sitemap.txt
    # ------------------------------------------------------------

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
        [
            'serie',
            'argomenti',
            'argomento',
            'tag',
            'tags',
        ]
    )

    if not topic_column:
        print("   ❌ ERRORE: nessuna colonna argomento trovata (cercavo 'Serie', 'Argomenti', 'Argomento', 'Tag', 'Tags').")
        return

    if 'id' not in df_catalogo.columns:
        print("   ❌ ERRORE: La colonna 'ID' non è presente nel foglio 'Catalogo'.")
        return

    print(f"   📊 Caricati {len(df_catalogo)} documenti dal foglio 'Catalogo' di dati.xlsx")
    print(f"   📊 Uso la colonna '{topic_column}' come fonte degli argomenti")

    # Rimuove eventuali pagine argomento generate in esecuzioni precedenti.
    os.makedirs(ARGOMENTI_DIR, exist_ok=True)
    clean_argomenti_dir()

    argomenti_map = {}

    for _, row in df_catalogo.iterrows():
        ami_id = pulisci_valore(row.get('id', ''))
        if not ami_id:
            continue

        titolo = pulisci_valore(row.get('titolo', ''))
        if not titolo:
            titolo = 'Senza titolo'

        data_raw = pulisci_valore(row.get('data', ''))
        if not data_raw:
            data_raw = pulisci_valore(row.get('anno', ''))

        data_form, data_ordine = formatta_data_sicura(data_raw)

        organizzazione = pulisci_valore(row.get('organizzazione', ''))
        tipo = pulisci_valore(row.get('tipo', ''))

        if organizzazione and tipo:
            badge = f'{organizzazione} · {tipo}'
        else:
            badge = organizzazione or tipo

        argomenti = split_argomenti(row.get(topic_column, ''))
        if not argomenti:
            continue

        seen_keys = set()

        for argomento in argomenti:
            key = normalize_key(argomento)

            if not key or key in seen_keys:
                continue

            seen_keys.add(key)

            doc = {
                'id': ami_id,
                'titolo': titolo,
                'data': data_form,
                'data_ordine': data_ordine,
                'badge': badge,
            }

            if key not in argomenti_map:
                argomenti_map[key] = {
                    'label': argomento,
                    'docs': [doc],
                }
            else:
                argomenti_map[key]['label'] = choose_label(
                    argomenti_map[key]['label'],
                    argomento
                )
                argomenti_map[key]['docs'].append(doc)

    if not argomenti_map:
        print('   ⚠️ Nessun argomento valido trovato.')
        return

    argomenti = list(argomenti_map.values())

    used_slugs = set()

    for item in argomenti:
        item['docs'].sort(
            key=lambda doc: (
                doc['data_ordine'],
                doc['titolo'].lower()
            )
        )
        item['num_doc'] = len(item['docs'])
        item['slug'] = make_slug(item['label'], used_slugs)

    print(f'   📊 Trovati {len(argomenti)} argomenti con documenti associati.')

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