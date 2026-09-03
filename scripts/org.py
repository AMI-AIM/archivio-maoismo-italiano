import os
import json
import hashlib
import pandas as pd

from core.utils import slugify, formatta_data, split_nomi
from core.site_config import site_path
from core.catalog_indexer import CatalogIndexer
from core.schema_generator import SchemaGenerator

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'build')

PLACEHOLDER_URL = site_path('immagini/profili/placeholder.webp')


def colore_hash(nome):
    hash_obj = hashlib.md5(nome.encode('utf-8'))
    hex_color = hash_obj.hexdigest()[:6]
    return f'#{hex_color}'


def get_iniziali(nome, max_lettere=2):
    parti = nome.split()
    if not parti:
        return '?'
    if len(parti) == 1:
        return parti[0][0].upper()
    return ''.join(p[0] for p in parti[:max_lettere]).upper()


def get_categoria_automatica(nome):
    nome_lower = nome.lower()
    if 'partito' in nome_lower or 'comunista' in nome_lower:
        return 'Partito'
    elif 'edizioni' in nome_lower or 'casa editrice' in nome_lower:
        return 'Casa editrice'
    elif 'servire il popolo' in nome_lower:
        return 'Organizzazione politica'
    elif 'oriente' in nome_lower and 'edizioni' not in nome_lower:
        return 'Centro di documentazione'
    elif 'centro' in nome_lower or 'informazione' in nome_lower:
        return 'Centro studi'
    elif 'università' in nome_lower or 'istituto' in nome_lower:
        return 'Istituto'
    elif 'collettivo' in nome_lower or 'gruppo' in nome_lower:
        return 'Collettivo'
    elif 'movimento' in nome_lower or 'fronte' in nome_lower:
        return 'Movimento'
    else:
        return 'Organizzazione'


def genera_organizzazioni():
    print("\n🏛️ Generazione delle pagine delle organizzazioni...")

    try:
        org_path = os.path.join(DATA_DIR, 'dati.xlsx')
        df_org = pd.read_excel(org_path, sheet_name='Organizzazioni', dtype=str).fillna('')
        df_org.columns = df_org.columns.str.strip().str.lower()
    except FileNotFoundError:
        print(f"   ❌ ERRORE: Non trovo '{org_path}'.")
        return
    except Exception as e:
        print(f"   ❌ ERRORE durante la lettura del foglio 'Organizzazioni' in dati.xlsx: {e}")
        return

    if df_org.empty:
        print("   ⚠️ Il foglio 'Organizzazioni' in dati.xlsx è vuoto.")
        return

    try:
        catalogo_path = os.path.join(DATA_DIR, 'dati.xlsx')
        df_catalogo = pd.read_excel(catalogo_path, sheet_name='Catalogo', dtype=str).fillna('')
        df_catalogo.columns = df_catalogo.columns.str.strip().str.lower()
    except FileNotFoundError:
        print(f"   ❌ ERRORE: Non trovo '{catalogo_path}'.")
        return
    except Exception as e:
        print(f"   ❌ ERRORE durante la lettura del foglio 'Catalogo' in dati.xlsx: {e}")
        return

    print(f"   📊 Caricate {len(df_org)} organizzazioni dal foglio 'Organizzazioni' di dati.xlsx")
    print(f"   📊 Caricati {len(df_catalogo)} documenti dal foglio 'Catalogo' di dati.xlsx")

    # ============================================================
    # CREAZIONE INDEXER (lookup O(1))
    # ============================================================
    print("   🔍 Creazione indici catalogo...")
    indexer = CatalogIndexer(df_catalogo)
    print("   ✅ Indici creati")

    organizzazioni = {}

    for _, row in df_org.iterrows():
        nome = str(row.get('nome', '')).strip()
        if not nome or nome in ['nan', 'None']:
            continue

        slug = slugify(nome)

        storia = str(row.get('storia', '')).strip()
        if storia in ['nan', 'None']:
            storia = ''

        categoria = str(row.get('categoria', '')).strip()
        if categoria in ['nan', 'None']:
            categoria = get_categoria_automatica(nome)

        fondazione = str(row.get('fondazione', '')).strip()
        if fondazione in ['nan', 'None']:
            fondazione = ''

        scioglimento = str(row.get('scioglimento', '')).strip()
        if scioglimento in ['nan', 'None']:
            scioglimento = ''

        immagine_raw = str(row.get('immagine', '')).strip()
        if immagine_raw and immagine_raw not in ['nan', 'None']:
            if immagine_raw.startswith('http://') or immagine_raw.startswith('https://'):
                immagine_url = immagine_raw
            else:
                immagine_url = site_path(f'immagini/profili/{immagine_raw}')
        else:
            immagine_url = None

        if fondazione and scioglimento:
            data_range = f"{fondazione} – {scioglimento}"
        elif fondazione:
            data_range = f"{fondazione} – "
        elif scioglimento:
            data_range = f"? – {scioglimento}"
        else:
            data_range = ''

        # ========================================================
        # DOCUMENTI COLLEGATI (con deduplicazione per ID)
        # ========================================================
        documenti = []
        visti = set()
        docs_rows = indexer.get_docs_for_organization(nome)

        for doc in docs_rows:
            ami_id = str(doc.get('id', '')).strip()
            if not ami_id or ami_id in ['nan', 'None']:
                continue
            if ami_id in visti:
                continue
            visti.add(ami_id)

            titolo = str(doc.get('titolo', 'Senza titolo')).strip()
            if titolo in ['nan', 'None']:
                titolo = 'Senza titolo'

            data_raw = str(doc.get('data', doc.get('anno', ''))).strip()
            if data_raw and data_raw not in ['nan', 'None']:
                data_form, data_ordine = formatta_data(data_raw)
            else:
                data_form = 'n.d.'
                data_ordine = (9999, 1, 1)

            ruoli = indexer.get_roles_for_organization(nome, doc)
            if ruoli:
                documenti.append({
                    'id': ami_id,
                    'titolo': titolo,
                    'data': data_form,
                    'data_ordine': data_ordine,
                    'ruoli': ruoli
                })

        if documenti:
            documenti.sort(key=lambda x: (x['data_ordine'], x['titolo']))
            organizzazioni[nome] = {
                'slug': slug,
                'storia': storia,
                'categoria': categoria,
                'fondazione': fondazione,
                'scioglimento': scioglimento,
                'data_range': data_range,
                'documenti': documenti,
                'immagine': immagine_url,
                'num_doc': len(documenti)
            }

    if not organizzazioni:
        print("   ⚠️ Nessuna organizzazione ha documenti associati nel catalogo.")
        return

    print(f"   📊 Trovate {len(organizzazioni)} organizzazioni con documenti associati.")

    org_dir = os.path.join(OUTPUT_DIR, 'organizzazioni')
    os.makedirs(org_dir, exist_ok=True)

    # ============================================================
    # SCHEDE INDIVIDUALI
    # ============================================================
    for nome, data in organizzazioni.items():
        slug = data['slug']
        file_path = os.path.join(org_dir, f'{slug}.md')

        storia_text = data['storia']
        if not storia_text:
            storia_text = f'<p><em>Scheda in fase di redazione. Nel frattempo, consulta i documenti collegati a {nome} qui sotto.</em></p>'
        elif '\n' in storia_text:
            storia_text = '<p>' + '</p><p>'.join(storia_text.split('\n')) + '</p>'

        # Genera schema JSON-LD per l'organizzazione
        schema = SchemaGenerator.organization_schema(
            nome=nome,
            storia=data['storia'],
            categoria=data['categoria'],
            immagine_url=data['immagine'],
            slug=data['slug'],
            num_doc=data['num_doc'],
            data_range=data['data_range']
        )
        schema_json = json.dumps(schema, ensure_ascii=False)

        frontmatter = f"""---
title: "{nome}"
description: "Documenti relativi a {nome}"
hide:
  - navigation
  - toc
  - title
---

<link rel="stylesheet" href="{site_path('stylesheets/soggetti.css')}">
<script type="application/ld+json">
{schema_json}
</script>
"""

        if data.get('immagine'):
            img_url = data['immagine']
            bio_section = f'''
<div class="org-bio-with-image">
    <div class="org-bio-text">
{storia_text}
    </div>
    <div class="org-bio-image">
        <img src="{img_url}" alt="Logo di {nome}, organizzazione nel maoismo italiano" class="org-bio-img" loading="lazy">
    </div>
</div>
'''
        else:
            bio_section = f'''
<div class="org-bio-full">
{storia_text}
</div>
'''

        dates_html = f'<div class="org-dates">{data["data_range"]}</div>' if data["data_range"] else ''

        content = f"""
<h1 class="org-name">{nome}</h1>
{dates_html}
{bio_section}
<h2 style="font-weight: bold; font-size: 1.2rem; margin: 1.5rem 0 0.5rem 0;">Documenti</h2>
<div class="catalogo-lista">
"""
        for doc in data['documenti']:
            ruoli_text = ", ".join(doc['ruoli'])
            doc_url = site_path(f"documenti/{doc['id']}/")
            content += f"""
<div class="doc-row">
    <div class="doc-data">{doc['data']}</div>
    <div class="doc-contenuto">
        <div class="doc-titolo"><a href="{doc_url}">{doc['titolo']}</a></div>
        <div class="doc-ruoli"><span class="ruolo-badge">{ruoli_text}</span></div>
    </div>
</div>
"""
        content += """
</div>
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter + content)
        print(f"   ✅ Creata scheda per {nome} → {slug}.md")

    # ============================================================
    # INDICE ORGANIZZAZIONI CON RICERCA + FILTRO ALFABETICO
    # ============================================================
    org_top = sorted(organizzazioni.items(), key=lambda x: x[1]['num_doc'], reverse=True)[:3]
    org_resto = sorted(
        [item for item in organizzazioni.items() if item[0] not in [o[0] for o in org_top]],
        key=lambda x: x[0].lower()
    )

    lettere_presenti = sorted(set([nome[0].upper() for nome, _ in org_resto]))
    tutte_lettere = [chr(i) for i in range(ord('A'), ord('Z') + 1)]

    lines = []
    lines.append('---')
    lines.append('title: "Organizzazioni"')
    lines.append('hide:')
    lines.append('  - navigation')
    lines.append('  - toc')
    lines.append('---')
    lines.append('')
    lines.append('# Organizzazioni in evidenza')
    lines.append('')

    if org_top:
        lines.append('<div class="top-row">')
        for nome, data in org_top:
            slug = data['slug']
            num_doc = data['num_doc']
            date_range = data['data_range']
            categoria = data['categoria']

            if data.get('immagine'):
                avatar_html = f'<img src="{data["immagine"]}" alt="{nome}" class="top-card-avatar-img" loading="lazy">'
            else:
                avatar_html = f'<img src="{PLACEHOLDER_URL}" alt="{nome}" class="top-card-avatar-img" loading="lazy">'

            count_text = "1 documento" if num_doc == 1 else f"{num_doc} documenti"

            lines.append(f'    <div class="top-card">')
            lines.append(f'        <a href="{slug}/" class="top-card-link">')
            lines.append(f'            <div class="top-card-image-wrapper">')
            lines.append(f'                {avatar_html}')
            lines.append(f'            </div>')
            lines.append(f'            <div class="top-card-text">')
            lines.append(f'                <div class="top-card-tipo">{categoria}</div>')
            lines.append(f'                <div class="top-card-name">{nome}</div>')
            lines.append(f'                <div class="top-card-dates">{date_range}</div>')
            lines.append(f'                <div class="top-card-count">{count_text}</div>')
            lines.append(f'            </div>')
            lines.append(f'        </a>')
            lines.append(f'    </div>')
        lines.append('</div>')

    lines.append('<div class="filtri-organizzazioni">')
    lines.append('    <div class="search-bar">')
    lines.append('        <input type="text" id="search-input" placeholder="🔍 Cerca per nome..." aria-label="Cerca organizzazioni">')
    lines.append('        <span id="search-counter" class="search-counter"></span>')
    lines.append('    </div>')
    lines.append('    <div class="alfabeto-bar">')
    lines.append('        <button class="lettera-btn lettera-btn--active" data-lettera="all">Tutte</button>')
    for lettera in tutte_lettere:
        if lettera in lettere_presenti:
            lines.append(f'        <button class="lettera-btn" data-lettera="{lettera}">{lettera}</button>')
        else:
            lines.append(f'        <button class="lettera-btn lettera-btn--disabled" data-lettera="{lettera}" disabled>{lettera}</button>')
    lines.append('    </div>')
    lines.append('</div>')

    if org_resto:
        lines.append('<div class="org-grid" id="org-grid">')
        for nome, data in org_resto:
            slug = data['slug']
            num_doc = data['num_doc']
            date_range = data['data_range']
            categoria = data['categoria']
            count_text = "1 documento" if num_doc == 1 else f"{num_doc} documenti"
            lettera = nome[0].upper()

            lines.append(f'<div class="org-card" data-lettera="{lettera}">')
            lines.append(f'    <a href="{slug}/" class="org-link">')
            lines.append(f'        <div class="org-tipo">{categoria}</div>')
            lines.append(f'        <div class="org-name">{nome}</div>')
            lines.append(f'        <div class="org-dates">{date_range}</div>')
            lines.append(f'        <div class="org-count">{count_text}</div>')
            lines.append(f'    </a>')
            lines.append(f'</div>')
        lines.append('</div>')
    else:
        lines.append('<p style="padding: 1rem 0; color: var(--md-default-fg-color--light);">Nessuna organizzazione aggiuntiva.</p>')

    lines.append('')
    lines.append('<script>')
    lines.append('(function() {')
    lines.append('    const searchInput = document.getElementById("search-input");')
    lines.append('    const searchCounter = document.getElementById("search-counter");')
    lines.append('    const grid = document.getElementById("org-grid");')
    lines.append('    const letteraBtns = document.querySelectorAll(".lettera-btn");')
    lines.append('')
    lines.append('    if (!grid) return;')
    lines.append('')
    lines.append('    const cards = grid.querySelectorAll(".org-card");')
    lines.append('')
    lines.append('    function filtra() {')
    lines.append('        const query = searchInput.value.toLowerCase().trim();')
    lines.append('        const letteraAttiva = document.querySelector(".lettera-btn--active");')
    lines.append('        const lettera = letteraAttiva ? letteraAttiva.dataset.lettera : "all";')
    lines.append('        let visibili = 0;')
    lines.append('')
    lines.append('        cards.forEach(card => {')
    lines.append('            const nome = card.querySelector(".org-name").textContent.toLowerCase();')
    lines.append('            const cardLettera = card.dataset.lettera;')
    lines.append('            const matchLettera = (lettera === "all" || cardLettera === lettera);')
    lines.append('            const matchRicerca = nome.includes(query);')
    lines.append('            const visibile = matchLettera && matchRicerca;')
    lines.append('')
    lines.append('            card.style.display = visibile ? "" : "none";')
    lines.append('')
    lines.append('            if (visibile) visibili++;')
    lines.append('        });')
    lines.append('')
    lines.append('        if (searchCounter) {')
    lines.append('            searchCounter.textContent = visibili + " organizzazioni";')
    lines.append('        }')
    lines.append('    }')
    lines.append('')
    lines.append('    searchInput.addEventListener("input", filtra);')
    lines.append('')
    lines.append('    letteraBtns.forEach(btn => {')
    lines.append('        btn.addEventListener("click", function() {')
    lines.append('            if (this.disabled) return;')
    lines.append('')
    lines.append('            letteraBtns.forEach(b => b.classList.remove("lettera-btn--active"));')
    lines.append('            this.classList.add("lettera-btn--active");')
    lines.append('            filtra();')
    lines.append('        });')
    lines.append('    });')
    lines.append('')
    lines.append('    filtra();')
    lines.append('})();')
    lines.append('</script>')
    lines.append('')
    lines.append('<link rel="stylesheet" href="../stylesheets/soggetti-indice.css">')
    lines.append('')

    index_content = "\n".join(lines)
    index_path = os.path.join(org_dir, 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)

    print(f"   ✅ Indice organizzazioni generato con {len(organizzazioni)} organizzazioni (top 3 in evidenza, resto con filtri).")


def main():
    print("🚀 Avvio del generatore di schede organizzazioni...")
    genera_organizzazioni()


if __name__ == "__main__":
    main()