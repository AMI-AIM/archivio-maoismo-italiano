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


def genera_persone():
    print("\n👤 Generazione delle pagine delle persone...")
    
    try:
        persone_path = os.path.join(DATA_DIR, 'dati.xlsx')
        df_persone = pd.read_excel(persone_path, sheet_name='Persone', dtype=str).fillna('')
        df_persone.columns = df_persone.columns.str.strip().str.lower()
    except FileNotFoundError:
        print(f"   ❌ ERRORE: Non trovo '{persone_path}'.")
        return
    except Exception as e:
        print(f"   ❌ ERRORE durante la lettura del foglio 'Persone' in dati.xlsx: {e}")
        return
    
    if df_persone.empty:
        print("   ⚠️ Il foglio 'Persone' in dati.xlsx è vuoto.")
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
    
    print(f"   📊 Caricate {len(df_persone)} persone dal foglio 'Persone' di dati.xlsx")
    print(f"   📊 Caricati {len(df_catalogo)} documenti dal foglio 'Catalogo' di dati.xlsx")
    
    # ============================================================
    # CREAZIONE INDEXER (lookup O(1))
    # ============================================================
    print("   🔍 Creazione indici catalogo...")
    indexer = CatalogIndexer(df_catalogo)
    print("   ✅ Indici creati")
    
    persone = {}
    
    for _, row in df_persone.iterrows():
        nome = str(row.get('nome', '')).strip()
        if not nome or nome in ['nan', 'None']:
            continue
        
        slug = slugify(nome)
        biografia = str(row.get('biografia', '')).strip()
        if biografia in ['nan', 'None']:
            biografia = ''
        nascita = str(row.get('nascita', '')).strip()
        if nascita in ['nan', 'None']:
            nascita = ''
        morte = str(row.get('morte', '')).strip()
        if morte in ['nan', 'None']:
            morte = ''
        
        immagine_raw = str(row.get('immagine', '')).strip()
        if immagine_raw and immagine_raw not in ['nan', 'None']:
            if immagine_raw.startswith('http://') or immagine_raw.startswith('https://'):
                immagine_url = immagine_raw
            else:
                immagine_url = site_path(f'immagini/profili/{immagine_raw}')
        else:
            immagine_url = None
        
        if nascita and morte:
            data_range = f"{nascita} – {morte}"
        elif nascita:
            data_range = f"{nascita} – "
        elif morte:
            data_range = f"? – {morte}"
        else:
            data_range = ''
        
        # Usa l'indexer per lookup O(1)
        documenti = []
        docs_rows = indexer.get_docs_for_person(nome)
        
        for doc in docs_rows:
            ami_id = str(doc.get('id', '')).strip()
            if not ami_id or ami_id in ['nan', 'None']:
                continue
            
            titolo = str(doc.get('titolo', 'Senza titolo')).strip()
            if titolo in ['nan', 'None']:
                titolo = 'Senza titolo'
            
            data_raw = str(doc.get('data', doc.get('anno', ''))).strip()
            if data_raw and data_raw not in ['nan', 'None']:
                data_form, data_ordine = formatta_data(data_raw)
            else:
                data_form = 'n.d.'
                data_ordine = (9999, 1, 1)
            
            # Usa indexer.get_roles_for_person() (O(1))
            ruoli = indexer.get_roles_for_person(nome, doc)
            
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
            persone[nome] = {
                'slug': slug,
                'biografia': biografia,
                'nascita': nascita,
                'morte': morte,
                'data_range': data_range,
                'documenti': documenti,
                'immagine': immagine_url,
                'num_doc': len(documenti)
            }
    
    if not persone:
        print("   ⚠️ Nessuna persona ha documenti associati nel catalogo.")
        return
    
    print(f"   📊 Trovate {len(persone)} persone con documenti associati.")
    
    persone_dir = os.path.join(OUTPUT_DIR, 'persone')
    os.makedirs(persone_dir, exist_ok=True)
    
    # ============================================================
    # SCHEDE INDIVIDUALI
    # ============================================================
    for nome, data in persone.items():
        slug = data['slug']
        file_path = os.path.join(persone_dir, f'{slug}.md')
        
        bio_text = data['biografia']
        if not bio_text:
            bio_text = f'<p><em>Scheda biografica in fase di redazione. Nel frattempo, consulta i documenti collegati a {nome} qui sotto.</em></p>'
        elif '\n' in bio_text:
            bio_text = '<p>' + '</p><p>'.join(bio_text.split('\n')) + '</p>'
        
        # Genera schema JSON-LD per la persona
        schema = SchemaGenerator.person_schema(
            nome=nome,
            biografia=data['biografia'],
            immagine_url=data['immagine'],
            slug=data['slug'],
            num_doc=data['num_doc'],
            data_range=data['data_range']
        )
        
        schema_json = json.dumps(schema, ensure_ascii=False)
        
        frontmatter = f"""---
title: "{nome}"
description: "Scheda biografica e documenti di {nome}"
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
            bio_section = f'''
<div class="person-bio-with-image">
    <div class="person-bio-text">
        {bio_text}
    </div>
    <div class="person-bio-image">
        <img src="{data['immagine']}" alt="Foto di {nome}, persona nel maoismo italiano" class="person-bio-img" loading="lazy">
    </div>
</div>
'''
        else:
            bio_section = f'''
<div class="person-bio-full">
    {bio_text}
</div>
'''
        
        content = f"""
<h1 class="person-name">{nome}</h1>

{f'<div class="person-dates">{data["data_range"]}</div>' if data["data_range"] else ''}

{bio_section}

<h2 style="font-weight: bold; font-size: 1.2rem; margin: 1.5rem 0 0.5rem 0;">Documenti</h2>

<div class="catalogo-lista">
"""
        
        for doc in data['documenti']:
            ruoli_text = ", ".join(doc['ruoli'])
            content += f"""
<div class="doc-row">
    <div class="doc-data">{doc['data']}</div>
    <div class="doc-contenuto">
        <div class="doc-titolo"><a href="{site_path(f"documenti/{doc['id']}/")}">{doc['titolo']}</a></div>
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
    # INDICE PERSONE CON RICERCA + FILTRO ALFABETICO
    # ============================================================
    
    persone_top = sorted(persone.items(), key=lambda x: x[1]['num_doc'], reverse=True)[:3]
    persone_resto = sorted(
        [item for item in persone.items() if item[0] not in [p[0] for p in persone_top]],
        key=lambda x: x[0].lower()
    )
    
    lettere_presenti = sorted(set([nome[0].upper() for nome, _ in persone_resto]))
    tutte_lettere = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
    
    lines = []
    lines.append('---')
    lines.append('title: "Persone"')
    lines.append('hide:')
    lines.append('  - navigation')
    lines.append('  - toc')
    lines.append('---')
    lines.append('')
    lines.append('# Persone in evidenza')
    lines.append('')
    
    if persone_top:
        lines.append('<div class="top-row">')
        for nome, data in persone_top:
            slug = data['slug']
            num_doc = data['num_doc']
            date_vita = data['data_range']
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
            lines.append(f'                <div class="top-card-name">{nome}</div>')
            lines.append(f'                <div class="top-card-dates">{date_vita}</div>')
            lines.append(f'                <div class="top-card-count">{count_text}</div>')
            lines.append(f'            </div>')
            lines.append(f'        </a>')
            lines.append(f'    </div>')
        lines.append('</div>')
    
    lines.append('<div class="filtri-persone">')
    lines.append('    <div class="search-bar">')
    lines.append('        <input type="text" id="search-input" placeholder="🔍 Cerca per nome..." aria-label="Cerca persone">')
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
    
    if persone_resto:
        lines.append('<div class="people-grid" id="people-grid">')
        for nome, data in persone_resto:
            slug = data['slug']
            num_doc = data['num_doc']
            date_vita = data['data_range']
            count_text = "1 documento" if num_doc == 1 else f"{num_doc} documenti"
            lettera = nome[0].upper()
            lines.append(f'<div class="people-card" data-lettera="{lettera}">')
            lines.append(f'    <a href="{slug}/" class="people-link">')
            lines.append(f'        <div class="people-name">{nome}</div>')
            lines.append(f'        <div class="people-dates">{date_vita}</div>')
            lines.append(f'        <div class="people-count">{count_text}</div>')
            lines.append(f'    </a>')
            lines.append(f'</div>')
        lines.append('</div>')
    else:
        lines.append('<p style="padding: 1rem 0; color: var(--md-default-fg-color--light);">Nessuna persona aggiuntiva.</p>')
    
    lines.append('')
    lines.append('<script>')
    lines.append('(function() {')
    lines.append('    const searchInput = document.getElementById("search-input");')
    lines.append('    const searchCounter = document.getElementById("search-counter");')
    lines.append('    const grid = document.getElementById("people-grid");')
    lines.append('    const letteraBtns = document.querySelectorAll(".lettera-btn");')
    lines.append('    if (!grid) return;')
    lines.append('    const cards = grid.querySelectorAll(".people-card");')
    lines.append('    function filtra() {')
    lines.append('        const query = searchInput.value.toLowerCase().trim();')
    lines.append('        const letteraAttiva = document.querySelector(".lettera-btn--active");')
    lines.append('        const lettera = letteraAttiva ? letteraAttiva.dataset.lettera : "all";')
    lines.append('        let visibili = 0;')
    lines.append('        cards.forEach(card => {')
    lines.append('            const nome = card.querySelector(".people-name").textContent.toLowerCase();')
    lines.append('            const cardLettera = card.dataset.lettera;')
    lines.append('            const matchLettera = (lettera === "all" || cardLettera === lettera);')
    lines.append('            const matchRicerca = nome.includes(query);')
    lines.append('            const visibile = matchLettera && matchRicerca;')
    lines.append('            card.style.display = visibile ? "" : "none";')
    lines.append('            if (visibile) visibili++;')
    lines.append('        });')
    lines.append('        if (searchCounter) {')
    lines.append('            searchCounter.textContent = visibili + " persone";')
    lines.append('        }')
    lines.append('    }')
    lines.append('    searchInput.addEventListener("input", filtra);')
    lines.append('    letteraBtns.forEach(btn => {')
    lines.append('        btn.addEventListener("click", function() {')
    lines.append('            if (this.disabled) return;')
    lines.append('            letteraBtns.forEach(b => b.classList.remove("lettera-btn--active"));')
    lines.append('            this.classList.add("lettera-btn--active");')
    lines.append('            filtra();')
    lines.append('        });')
    lines.append('    });')
    lines.append('    filtra();')
    lines.append('})();')
    lines.append('</script>')
    lines.append('')
    
    lines.append('<link rel="stylesheet" href="../stylesheets/soggetti-indice.css">')
    lines.append('')
    
    index_content = "\n".join(lines)
    
    index_path = os.path.join(persone_dir, 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"   ✅ Indice persone generato con {len(persone)} persone (top 3 in evidenza, resto con filtri).")


def main():
    print("🚀 Avvio del generatore di schede persone...")
    genera_persone()


if __name__ == "__main__":
    main()