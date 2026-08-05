import os
import hashlib
import pandas as pd
from core.utils import slugify, formatta_data, split_nomi

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'build')

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
                immagine_url = f'/archivio-maoismo-italiano/immagini/profili/{immagine_raw}'
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
            
            autore_raw = str(doc.get('autore', '')).strip()
            if autore_raw and autore_raw not in ['nan', 'None']:
                autori = split_nomi(autore_raw)
                if nome in autori:
                    ruoli.append('autore')
            
            persone_collegate = str(doc.get('persone_collegate', '')).strip()
            if persone_collegate and persone_collegate not in ['nan', 'None']:
                collegati = split_nomi(persone_collegate)
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
        
        frontmatter = f"""---
title: "{nome}"
description: "Scheda biografica e documenti di {nome}"
hide:
  - navigation
  - toc
  - title
---
"""
        
        if data.get('immagine'):
            bio_section = f'''
<div class="person-bio-with-image">
    <div class="person-bio-text">
        {bio_text}
    </div>
    <div class="person-bio-image">
        <img src="{data['immagine']}" alt="{nome}" class="person-bio-img">
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
<div class="person-name">{nome}</div>

{f'<div class="person-dates">{data["data_range"]}</div>' if data["data_range"] else ''}

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
.person-name { font-size: 2.4rem; font-weight: 700; margin: 0 0 0.2rem 0; color: var(--md-primary-fg-color); }
.person-dates { font-size: 1rem; color: var(--md-default-fg-color--light); margin: 0 0 0.8rem 0; font-weight: 400; }

/* BIOGRAFIA CON FOTO (testo a sinistra, foto a destra) */
.person-bio-with-image {
    display: flex;
    gap: 1.5rem;
    margin: 1rem 0 1.5rem 0;
    padding: 1rem;
    background: var(--md-code-bg-color);
    border-radius: 8px;
    border-left: 4px solid var(--md-primary-fg-color);
    align-items: flex-start;
}

.person-bio-text {
    flex: 1;
    min-width: 0;
}

.person-bio-text p {
    margin: 0.5rem 0;
}

.person-bio-image {
    flex: 0 0 360px;
    width: 360px;
    height: auto;
    max-height: 400px;
    overflow: hidden;
    border-radius: 8px;
    flex-shrink: 0;
}

.person-bio-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

/* BIOGRAFIA SENZA FOTO (tutta larghezza) */
.person-bio-full {
    margin: 1rem 0 1.5rem 0;
    padding: 1rem;
    background: var(--md-code-bg-color);
    border-radius: 8px;
    border-left: 4px solid var(--md-primary-fg-color);
}

.person-bio-full p {
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
    .person-bio-with-image {
        flex-direction: column;
        align-items: center;
    }
    .person-bio-image {
        flex: 0 0 auto;
        width: 100%;
        max-width: 360px;
        max-height: 300px;
    }
    .doc-row { flex-direction: column; gap: 0.1rem; padding: 0.6rem 0.2rem; }
    .doc-data { flex: 0 0 auto; white-space: normal; font-size: 0.8rem; }
    .person-name { font-size: 1.6rem; }
    .person-dates { font-size: 0.85rem; }
}
</style>
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
    
    lines.append('<style>')
    lines.append('.top-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 2rem; }')
    lines.append('.top-card { aspect-ratio: 1 / 1; background: var(--md-code-bg-color); border-radius: 12px; border: 1px solid var(--md-default-fg-color--lightest); overflow: hidden; transition: transform 0.2s, box-shadow 0.2s; padding: 0; }')
    lines.append('.top-card:hover { transform: translateY(-4px); box-shadow: 0 6px 16px rgba(0,0,0,0.08); }')
    lines.append('.top-card-link { text-decoration: none; color: inherit; display: flex; flex-direction: column; width: 100%; height: 100%; }')
    lines.append('.top-card-image-wrapper { flex: 1; overflow: hidden; background: var(--md-code-bg-color); display: flex; }')
    lines.append('.top-card-avatar-img { width: 100%; height: 100%; object-fit: cover; display: block; }')
    lines.append('.top-card-text { padding: 0.6rem 1rem 0.8rem 1rem; background: var(--md-code-bg-color); border-top: 1px solid var(--md-default-fg-color--lightest); flex-shrink: 0; }')
    lines.append('.top-card-name { font-size: 1rem; font-weight: 600; color: var(--md-default-fg-color); line-height: 1.2; }')
    lines.append('.top-card-dates { font-size: 0.8rem; color: var(--md-default-fg-color--light); }')
    lines.append('.top-card-count { font-size: 0.75rem; color: var(--md-default-fg-color--light); font-weight: 400; }')
    lines.append('.filtri-persone { margin: 1rem 0 1.5rem 0; padding: 0.8rem 1rem; background: var(--md-code-bg-color); border-radius: 8px; border: 1px solid var(--md-default-fg-color--lightest); }')
    lines.append('.search-bar { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.6rem; }')
    lines.append('.search-bar input { flex: 1; padding: 0.5rem 0.8rem; border: 1px solid var(--md-default-fg-color--lightest); border-radius: 6px; background: var(--md-default-bg-color); color: var(--md-default-fg-color); font-size: 0.95rem; outline: none; transition: border-color 0.2s; }')
    lines.append('.search-bar input:focus { border-color: var(--md-primary-fg-color); }')
    lines.append('.search-counter { font-size: 0.8rem; color: var(--md-default-fg-color--light); white-space: nowrap; font-weight: 500; }')
    lines.append('.alfabeto-bar { display: flex; flex-wrap: wrap; gap: 0.2rem; }')
    lines.append('.lettera-btn { background: transparent; border: 1px solid var(--md-default-fg-color--lightest); border-radius: 4px; padding: 0.2rem 0.5rem; font-size: 0.75rem; font-weight: 600; color: var(--md-default-fg-color); cursor: pointer; transition: background 0.15s, color 0.15s, border-color 0.15s; min-width: 28px; text-align: center; }')
    lines.append('.lettera-btn:hover:not(.lettera-btn--disabled) { background: var(--md-primary-fg-color); color: #ffffff; border-color: var(--md-primary-fg-color); }')
    lines.append('.lettera-btn--active { background: var(--md-primary-fg-color); color: #ffffff !important; border-color: var(--md-primary-fg-color); }')
    lines.append('.lettera-btn--disabled { opacity: 0.3; cursor: not-allowed; }')
    lines.append('.people-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 0.5rem; }')
    lines.append('.people-card { background: var(--md-code-bg-color); border-radius: 8px; padding: 1rem 1.2rem; transition: background-color 0.2s, transform 0.15s, box-shadow 0.2s; border: 1px solid var(--md-default-fg-color--lightest); min-height: 80px; display: flex; align-items: center; }')
    lines.append('.people-card:hover { background: var(--md-default-bg-color); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }')
    lines.append('.people-link { text-decoration: none; display: flex; flex-direction: column; width: 100%; gap: 0.05rem; }')
    lines.append('.people-name { font-size: 0.95rem; font-weight: 600; color: var(--md-default-fg-color); line-height: 1.3; }')
    lines.append('.people-dates { font-size: 0.7rem; color: var(--md-default-fg-color--light); }')
    lines.append('.people-count { font-size: 0.75rem; color: var(--md-default-fg-color--light); }')
    lines.append('@media (max-width: 900px) { .people-grid { grid-template-columns: repeat(2, 1fr); } }')
    lines.append('@media (max-width: 768px) { .top-row { grid-template-columns: 1fr; gap: 1rem; } .top-card { aspect-ratio: auto; min-height: 200px; } .top-card-text { padding: 0.4rem 0.8rem 0.6rem 0.8rem; } .top-card-name { font-size: 0.95rem; } .search-bar { flex-direction: column; align-items: stretch; gap: 0.4rem; } .search-counter { text-align: right; } .alfabeto-bar { justify-content: center; gap: 0.15rem; } .lettera-btn { font-size: 0.7rem; padding: 0.15rem 0.4rem; min-width: 24px; } }')
    lines.append('@media (max-width: 600px) { .people-grid { grid-template-columns: 1fr; } .people-name { font-size: 0.9rem; } .people-dates { font-size: 0.65rem; } }')
    lines.append('</style>')
    
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