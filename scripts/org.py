import os
import hashlib
import pandas as pd
from scripts.config import DATA_DIR, BUILD_DIR
from scripts.core.utils import slugify, formatta_data, split_nomi

PLACEHOLDER_URL = '/archivio-maoismo-italiano/immagini/profili/placeholder.webp'

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
        org_path = DATA_DIR / 'dati.xlsx'
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
        catalogo_path = DATA_DIR / 'dati.xlsx'
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
                immagine_url = f'/archivio-maoismo-italiano/immagini/profili/{immagine_raw}'
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

        documenti = []

        for _, doc in df_catalogo.iterrows():
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

            ruoli = []

            org_raw = str(doc.get('organizzazione', '')).strip()
            if org_raw and org_raw not in ['nan', 'None']:
                orgs = split_nomi(org_raw)
                if nome in orgs:
                    ruoli.append('pubblicato da')

            autore_raw = str(doc.get('autore', '')).strip()
            if autore_raw and autore_raw not in ['nan', 'None']:
                autori = split_nomi(autore_raw)
                if nome in autori:
                    ruoli.append('autore')

            org_collegate = str(doc.get('organizzazioni_collegate', '')).strip()
            if org_collegate and org_collegate not in ['nan', 'None']:
                collegati = split_nomi(org_collegate)
                if nome in collegati:
                    ruoli.append('menzionato')

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

    org_dir = BUILD_DIR / 'organizzazioni'
    org_dir.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # SCHEDE INDIVIDUALI
    # ============================================================
    for nome, data in organizzazioni.items():
        slug = data['slug']
        file_path = org_dir / f'{slug}.md'

        storia_text = data['storia']
        if not storia_text:
            storia_text = f'<p><em>Scheda in fase di redazione. Nel frattempo, consulta i documenti collegati a {nome} qui sotto.</em></p>'
        elif '\n' in storia_text:
            storia_text = '<p>' + '</p><p>'.join(storia_text.split('\n')) + '</p>'

        frontmatter = f"""---
title: " "
description: "Documenti relativi a {nome}"
hide:
  - navigation
  - toc
  - title
---
"""

        if data.get('immagine'):
            bio_section = f'''
<div class="org-bio-with-image">
    <div class="org-bio-text">
        {storia_text}
    </div>
    <div class="org-bio-image">
        <img src="{data['immagine']}" alt="{nome}" class="org-bio-img">
    </div>
</div>
'''
        else:
            bio_section = f'''
<div class="org-bio-full">
    {storia_text}
</div>
'''

        content = f"""
<div class="org-name">{nome}</div>

{f'<div class="org-dates">{data["data_range"]}</div>' if data["data_range"] else ''}

{bio_section}

<h3 style="font-weight: bold; font-size: 1.2rem; margin: 1.5rem 0 0.5rem 0;">Documenti</h3>

<div class="catalogo-lista">
"""

        for doc in data['documenti']:
            ruoli_text = ", ".join(doc['ruoli'])
            content += f"""
<div class="doc-row">
    <div class="doc-data">{doc['data']}</div>
    <div class="doc-contenuto">
        <div class="doc-titolo"><a href="/archivio-maoismo-italiano/documenti/{doc['id']}/">{doc['titolo']}</a></div>
        <div class="doc-ruoli"><span class="ruolo-badge">{ruoli_text}</span></div>
    </div>
</div>
"""

        content += """
</div>

<style>
.org-name { font-size: 2.4rem; font-weight: 700; margin: 0 0 0.2rem 0; color: var(--md-primary-fg-color); }
.org-dates { font-size: 1rem; color: var(--md-default-fg-color--light); margin: 0 0 0.8rem 0; font-weight: 400; }

/* STORIA CON FOTO (testo a sinistra, foto a destra) */
.org-bio-with-image {
    display: flex;
    gap: 1.5rem;
    margin: 1rem 0 1.5rem 0;
    padding: 1rem;
    background: var(--md-code-bg-color);
    border-radius: 8px;
    border-left: 4px solid var(--md-primary-fg-color);
    align-items: flex-start;
}

.org-bio-text {
    flex: 1;
    min-width: 0;
}

.org-bio-text p {
    margin: 0.5rem 0;
}

.org-bio-image {
    flex: 0 0 360px;
    width: 360px;
    height: auto;
    max-height: 400px;
    overflow: hidden;
    border-radius: 8px;
    flex-shrink: 0;
}

.org-bio-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

/* STORIA SENZA FOTO (tutta larghezza) */
.org-bio-full {
    margin: 1rem 0 1.5rem 0;
    padding: 1rem;
    background: var(--md-code-bg-color);
    border-radius: 8px;
    border-left: 4px solid var(--md-primary-fg-color);
}

.org-bio-full p {
    margin: 0.5rem 0;
}

.catalogo-lista { display: flex; flex-direction: column; gap: 0.25rem; margin-top: 0.5rem; }
.doc-row { display: flex; align-items: flex-start; padding: 0.4rem 0.6rem; border-bottom: 1px solid var(--md-default-fg-color--lightest); transition: background-color 0.15s; gap: 1.5rem; }
.doc-row:hover { background-color: var(--md-code-bg-color); }
.doc-data { flex: 0 0 140px; font-size: 0.9rem; color: var(--md-primary-fg-color); font-weight: 500; white-space: nowrap; padding-top: 0.05rem; }
.doc-contenuto { flex: 1; min-width: 0; }
.doc-titolo { font-size: 1rem; font-weight: 500; }
.doc-titolo a { text-decoration: none; color: var(--md-default-fg-color); }
.doc-titolo a:hover { text-decoration: underline; color: var(--md-primary-fg-color); }
.doc-ruoli { margin-top: 0.1rem; }
.ruolo-badge { display: inline-block; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #ffffff !important; background: var(--md-primary-fg-color); padding: 0.05rem 0.6rem; border-radius: 4px; }

@media (max-width: 768px) {
    .org-bio-with-image {
        flex-direction: column;
        align-items: center;
    }
    .org-bio-image {
        flex: 0 0 auto;
        width: 100%;
        max-width: 360px;
        max-height: 300px;
    }
    .doc-row { flex-direction: column; gap: 0.1rem; padding: 0.6rem 0.2rem; }
    .doc-data { flex: 0 0 auto; white-space: normal; font-size: 0.8rem; }
    .org-name { font-size: 1.6rem; }
    .org-dates { font-size: 0.85rem; }
}
</style>
"""

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter + content)

        print(f"   ✅ Creata scheda per {nome} → {slug}.md")

    # ============================================================
    # INDICE ORGANIZZAZIONI
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
    lines.append('    if (!grid) return;')
    lines.append('    const cards = grid.querySelectorAll(".org-card");')
    lines.append('    function filtra() {')
    lines.append('        const query = searchInput.value.toLowerCase().trim();')
    lines.append('        const letteraAttiva = document.querySelector(".lettera-btn--active");')
    lines.append('        const lettera = letteraAttiva ? letteraAttiva.dataset.lettera : "all";')
    lines.append('        let visibili = 0;')
    lines.append('        cards.forEach(card => {')
    lines.append('            const nome = card.querySelector(".org-name").textContent.toLowerCase();')
    lines.append('            const cardLettera = card.dataset.lettera;')
    lines.append('            const matchLettera = (lettera === "all" || cardLettera === lettera);')
    lines.append('            const matchRicerca = nome.includes(query);')
    lines.append('            const visibile = matchLettera && matchRicerca;')
    lines.append('            card.style.display = visibile ? "" : "none";')
    lines.append('            if (visibile) visibili++;')
    lines.append('        });')
    lines.append('        if (searchCounter) {')
    lines.append('            searchCounter.textContent = visibili + " organizzazioni";')
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

    lines.append('<style>')
    lines.append('.top-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 2rem; }')
    lines.append('.top-card { aspect-ratio: 1 / 1; background: var(--md-code-bg-color); border-radius: 12px; border: 1px solid var(--md-default-fg-color--lightest); overflow: hidden; transition: transform 0.2s, box-shadow 0.2s; padding: 0; }')
    lines.append('.top-card:hover { transform: translateY(-4px); box-shadow: 0 6px 16px rgba(0,0,0,0.08); }')
    lines.append('.top-card-link { text-decoration: none; color: inherit; display: flex; flex-direction: column; width: 100%; height: 100%; }')
    lines.append('.top-card-image-wrapper { flex: 1; overflow: hidden; background: var(--md-code-bg-color); display: flex; }')
    lines.append('.top-card-avatar-img { width: 100%; height: 100%; object-fit: cover; display: block; }')
    lines.append('.top-card-text { padding: 0.6rem 1rem 0.8rem 1rem; background: var(--md-code-bg-color); border-top: 1px solid var(--md-default-fg-color--lightest); flex-shrink: 0; }')
    lines.append('.top-card-tipo { font-size: 0.6rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #ffffff !important; background: var(--md-primary-fg-color); padding: 0.05rem 0.6rem; border-radius: 4px; display: inline-block; width: fit-content; margin-bottom: 0.15rem; }')
    lines.append('.top-card-name { font-size: 1rem; font-weight: 600; color: var(--md-default-fg-color); line-height: 1.2; }')
    lines.append('.top-card-dates { font-size: 0.8rem; color: var(--md-default-fg-color--light); }')
    lines.append('.top-card-count { font-size: 0.75rem; color: var(--md-default-fg-color--light); font-weight: 400; }')
    lines.append('.filtri-organizzazioni { margin: 1rem 0 1.5rem 0; padding: 0.8rem 1rem; background: var(--md-code-bg-color); border-radius: 8px; border: 1px solid var(--md-default-fg-color--lightest); }')
    lines.append('.search-bar { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.6rem; }')
    lines.append('.search-bar input { flex: 1; padding: 0.5rem 0.8rem; border: 1px solid var(--md-default-fg-color--lightest); border-radius: 6px; background: var(--md-default-bg-color); color: var(--md-default-fg-color); font-size: 0.95rem; outline: none; transition: border-color 0.2s; }')
    lines.append('.search-bar input:focus { border-color: var(--md-primary-fg-color); }')
    lines.append('.search-counter { font-size: 0.8rem; color: var(--md-default-fg-color--light); white-space: nowrap; font-weight: 500; }')
    lines.append('.alfabeto-bar { display: flex; flex-wrap: wrap; gap: 0.2rem; }')
    lines.append('.lettera-btn { background: transparent; border: 1px solid var(--md-default-fg-color--lightest); border-radius: 4px; padding: 0.2rem 0.5rem; font-size: 0.75rem; font-weight: 600; color: var(--md-default-fg-color); cursor: pointer; transition: background 0.15s, color 0.15s, border-color 0.15s; min-width: 28px; text-align: center; }')
    lines.append('.lettera-btn:hover:not(.lettera-btn--disabled) { background: var(--md-primary-fg-color); color: #ffffff; border-color: var(--md-primary-fg-color); }')
    lines.append('.lettera-btn--active { background: var(--md-primary-fg-color); color: #ffffff !important; border-color: var(--md-primary-fg-color); }')
    lines.append('.lettera-btn--disabled { opacity: 0.3; cursor: not-allowed; }')
    lines.append('.org-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 0.5rem; }')
    lines.append('.org-card { background: var(--md-code-bg-color); border-radius: 8px; padding: 1rem 1.2rem; transition: background-color 0.2s, transform 0.15s, box-shadow 0.2s; border: 1px solid var(--md-default-fg-color--lightest); min-height: 80px; display: flex; align-items: center; }')
    lines.append('.org-card:hover { background: var(--md-default-bg-color); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }')
    lines.append('.org-link { text-decoration: none; display: flex; flex-direction: column; width: 100%; gap: 0.05rem; }')
    lines.append('.org-tipo { font-size: 0.6rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #ffffff !important; background: var(--md-primary-fg-color); padding: 0.05rem 0.6rem; border-radius: 4px; display: inline-block; width: fit-content; }')
    lines.append('.org-name { font-size: 0.95rem; font-weight: 600; color: var(--md-default-fg-color); line-height: 1.3; }')
    lines.append('.org-dates { font-size: 0.7rem; color: var(--md-default-fg-color--light); }')
    lines.append('.org-count { font-size: 0.75rem; color: var(--md-default-fg-color--light); }')
    lines.append('@media (max-width: 900px) { .org-grid { grid-template-columns: repeat(2, 1fr); } }')
    lines.append('@media (max-width: 768px) { .top-row { grid-template-columns: 1fr; gap: 1rem; } .top-card { aspect-ratio: auto; min-height: 200px; } .top-card-text { padding: 0.4rem 0.8rem 0.6rem 0.8rem; } .top-card-name { font-size: 0.95rem; } .search-bar { flex-direction: column; align-items: stretch; gap: 0.4rem; } .search-counter { text-align: right; } .alfabeto-bar { justify-content: center; gap: 0.15rem; } .lettera-btn { font-size: 0.7rem; padding: 0.15rem 0.4rem; min-width: 24px; } }')
    lines.append('@media (max-width: 600px) { .org-grid { grid-template-columns: 1fr; } .org-name { font-size: 0.9rem; } .org-dates { font-size: 0.65rem; } }')
    lines.append('</style>')

    index_content = "\n".join(lines)

    index_path = org_dir / 'index.md'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)

    print(f"   ✅ Indice organizzazioni generato con {len(organizzazioni)} organizzazioni (top 3 in evidenza, resto con filtri).")

def main():
    print("🚀 Avvio del generatore di schede organizzazioni...")
    genera_organizzazioni()

if __name__ == "__main__":
    main()