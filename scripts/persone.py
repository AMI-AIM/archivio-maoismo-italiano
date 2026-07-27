import os
import re
import hashlib
import pandas as pd
from collections import Counter
from core.utils import slugify, formatta_data, split_nomi

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'docs')


def colore_hash(nome):
    """Genera un colore uniforme per le iniziali in base al nome."""
    hash_obj = hashlib.md5(nome.encode('utf-8'))
    hex_color = hash_obj.hexdigest()[:6]
    return f'#{hex_color}'


def get_iniziali(nome, max_lettere=2):
    """Estrae le iniziali da un nome."""
    parti = nome.split()
    if not parti:
        return '?'
    if len(parti) == 1:
        return parti[0][0].upper()
    return ''.join(p[0] for p in parti[:max_lettere]).upper()


def genera_persone():
    print("\n👤 Generazione delle pagine delle persone...")
    
    try:
        persone_path = os.path.join(DATA_DIR, 'persone.xlsx')
        df_persone = pd.read_excel(persone_path, dtype=str).fillna('')
        df_persone.columns = df_persone.columns.str.strip().str.lower()
    except FileNotFoundError:
        print(f"   ❌ ERRORE: Non trovo '{persone_path}'.")
        return
    except Exception as e:
        print(f"   ❌ ERRORE durante la lettura di persone.xlsx: {e}")
        return
    
    if df_persone.empty:
        print("   ⚠️ Il file persone.xlsx è vuoto.")
        return
    
    try:
        catalogo_path = os.path.join(DATA_DIR, 'catalogo.xlsx')
        df_catalogo = pd.read_excel(catalogo_path, dtype=str).fillna('')
        df_catalogo.columns = df_catalogo.columns.str.strip().str.lower()
    except FileNotFoundError:
        print(f"   ❌ ERRORE: Non trovo '{catalogo_path}'.")
        return
    except Exception as e:
        print(f"   ❌ ERRORE durante la lettura di catalogo.xlsx: {e}")
        return
    
    print(f"   📊 Caricate {len(df_persone)} persone da data/persone.xlsx")
    print(f"   📊 Caricati {len(df_catalogo)} documenti da data/catalogo.xlsx")
    
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
                data_form, _ = formatta_data(data_raw)
            else:
                data_form = 'n.d.'
            
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
                    'ruoli': ruoli
                })
        
        if documenti:
            documenti.sort(key=lambda x: (x['data'] == 'n.d.', x['data'], x['titolo']))
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
    # GENERA SCHEDE INDIVIDUALI
    # ============================================================
    for nome, data in persone.items():
        slug = data['slug']
        file_path = os.path.join(persone_dir, f'{slug}.md')
        
        bio_text = data['biografia']
        if not bio_text:
            bio_text = f'<p><em>Biografia in costruzione. Scrivi qui la storia di {nome}.</em></p>'
        elif '\n' in bio_text:
            bio_text = '<p>' + '</p><p>'.join(bio_text.split('\n')) + '</p>'
        
        frontmatter = f"""---
title: "{nome}"
description: "Scheda biografica e documenti di {nome}"
hide:
  - navigation
  - toc
---
"""
        
        content = f"""
<h1 class="person-name">{nome}</h1>

{f'<div class="person-dates">{data["data_range"]}</div>' if data["data_range"] else ''}

<div class="person-bio">
    {bio_text}
</div>

## 📄 Documenti presenti nell'AMI

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
.person-name {
    font-size: 2.4rem;
    font-weight: 700;
    margin: 0.5rem 0 0 0;
    color: var(--md-primary-fg-color);
}

.person-dates {
    font-size: 1rem;
    color: var(--md-default-fg-color--light);
    margin: 0 0 1rem 0;
    font-weight: 400;
    letter-spacing: 0.02em;
}

.person-bio {
    margin: 1.5rem 0;
    padding: 1rem;
    background: var(--md-code-bg-color);
    border-radius: 8px;
    border-left: 4px solid var(--md-primary-fg-color);
}

.person-bio p {
    margin: 0.5rem 0;
}

.catalogo-lista {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin-top: 0.5rem;
}

.doc-row {
    display: flex;
    align-items: flex-start;
    padding: 0.4rem 0.6rem;
    border-bottom: 1px solid var(--md-default-fg-color--lightest);
    transition: background-color 0.15s;
    gap: 1.5rem;
}

.doc-row:hover {
    background-color: var(--md-code-bg-color);
}

.doc-data {
    flex: 0 0 140px;
    font-size: 0.9rem;
    color: var(--md-primary-fg-color);
    font-weight: 500;
    white-space: nowrap;
    padding-top: 0.05rem;
}

.doc-contenuto {
    flex: 1;
    min-width: 0;
}

.doc-titolo {
    font-size: 1rem;
    font-weight: 500;
}

.doc-titolo a {
    text-decoration: none;
    color: var(--md-default-fg-color);
}

.doc-titolo a:hover {
    text-decoration: underline;
    color: var(--md-primary-fg-color);
}

.doc-ruoli {
    margin-top: 0.1rem;
}

.ruolo-badge {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #ffffff !important;
    background: var(--md-primary-fg-color);
    padding: 0.05rem 0.6rem;
    border-radius: 4px;
}

@media (max-width: 600px) {
    .doc-row {
        flex-direction: column;
        gap: 0.1rem;
        padding: 0.6rem 0.2rem;
    }
    .doc-data {
        flex: 0 0 auto;
        white-space: normal;
        font-size: 0.8rem;
    }
    .person-name {
        font-size: 1.6rem;
    }
    .person-dates {
        font-size: 0.85rem;
    }
}
</style>
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter + content)
        
        print(f"   ✅ Creata scheda per {nome} → {slug}.md")
    
    # ============================================================
    # INDICE PERSONE CON TOP 3
    # ============================================================
    
    persone_ordinate = sorted(persone.items(), key=lambda x: x[1]['num_doc'], reverse=True)
    persone_top = persone_ordinate[:3]
    persone_resto = persone_ordinate[3:]
    
    index_content = """---
title: "Persone"
hide:
  - navigation
  - toc
---

# Persone

"""
    
    if persone_top:
        index_content += '<div class="top-row">\n'
        for nome, data in persone_top:
            slug = data['slug']
            num_doc = data['num_doc']
            date_vita = data['data_range']
            iniziali = get_iniziali(nome)
            colore = colore_hash(nome)
            
            if data.get('immagine'):
                avatar_html = f'<img src="{data["immagine"]}" alt="{nome}" class="top-card-avatar-img">'
            else:
                avatar_html = f'<div class="top-card-avatar" style="background-color: {colore};"><span class="top-card-initials">{iniziali}</span></div>'
            
            count_text = "1 documento" if num_doc == 1 else f"{num_doc} documenti"
            
            index_content += f'''
    <div class="top-card">
        <a href="{slug}/" class="top-card-link">
            {avatar_html}
            <div class="top-card-name">{nome}</div>
            <div class="top-card-dates">{date_vita}</div>
            <div class="top-card-count">{count_text}</div>
        </a>
    </div>
'''
        index_content += '</div>\n'
    
    if persone_resto:
        index_content += '<div class="people-grid">\n'
        for nome, data in persone_resto:
            slug = data['slug']
            num_doc = data['num_doc']
            date_vita = data['data_range']
            count_text = "1 documento" if num_doc == 1 else f"{num_doc} documenti"
            
            index_content += f'''
<div class="people-card">
    <a href="{slug}/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">{nome}</div>
        <div class="people-dates">{date_vita}</div>
        <div class="people-count">{count_text}</div>
    </a>
</div>
'''
        index_content += '</div>\n'
    
    index_content += """
<style>
/* ============================================================
   TOP ROW
   ============================================================ */
.top-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    margin-bottom: 2.5rem;
}

.top-card {
    background: var(--md-code-bg-color);
    border-radius: 12px;
    border: 1px solid var(--md-default-fg-color--lightest);
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
    text-align: center;
    padding: 1.5rem 0.5rem;
    min-height: 220px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.top-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.08);
}

.top-card-link {
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
}

.top-card-avatar {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.top-card-avatar-img {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
}

.top-card-initials {
    font-size: 2.2rem;
    font-weight: 600;
    color: #ffffff;
    text-shadow: 0 1px 4px rgba(0,0,0,0.2);
    text-transform: uppercase;
}

.top-card-name {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--md-default-fg-color);
    line-height: 1.3;
}

.top-card-dates {
    font-size: 0.85rem;
    color: var(--md-default-fg-color--light);
}

.top-card-count {
    font-size: 0.75rem;
    font-weight: 600;
    color: #ffffff !important;
    background: var(--md-primary-fg-color);
    padding: 0.15rem 0.8rem;
    border-radius: 20px;
    display: inline-block;
}

.people-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-top: 1rem;
}

.people-card {
    background: var(--md-code-bg-color);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    transition: background-color 0.2s, transform 0.15s, box-shadow 0.2s;
    border: 1px solid var(--md-default-fg-color--lightest);
    min-height: 100px;
    display: flex;
    align-items: center;
}

.people-card:hover {
    background: var(--md-default-bg-color);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.people-link {
    text-decoration: none;
    display: flex;
    flex-direction: column;
    width: 100%;
    gap: 0.1rem;
}

.people-tipo {
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #ffffff !important;
    background: var(--md-primary-fg-color);
    padding: 0.05rem 0.6rem;
    border-radius: 4px;
    display: inline-block;
    width: fit-content;
}

.people-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--md-default-fg-color);
    line-height: 1.3;
    word-break: break-word;
}

.people-dates {
    font-size: 0.7rem;
    color: var(--md-default-fg-color--light);
    margin-top: 0.05rem;
}

.people-count {
    font-size: 0.75rem;
    color: var(--md-default-fg-color--light);
    margin-top: 0.1rem;
}

@media (max-width: 900px) {
    .people-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .top-row {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
    .top-card {
        min-height: 180px;
        padding: 1rem 0.5rem;
    }
    .top-card-avatar,
    .top-card-avatar-img {
        width: 70px;
        height: 70px;
    }
    .top-card-initials {
        font-size: 1.8rem;
    }
    .top-card-name {
        font-size: 0.95rem;
    }
}

@media (max-width: 600px) {
    .people-grid {
        grid-template-columns: 1fr;
    }
    .people-name {
        font-size: 0.9rem;
    }
    .people-dates {
        font-size: 0.65rem;
    }
}
</style>
"""
    
    index_path = os.path.join(persone_dir, 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"   ✅ Indice persone generato con {len(persone)} persone (top 3 in evidenza).")


def main():
    print("🚀 Avvio del generatore di schede persone...")
    genera_persone()


if __name__ == "__main__":
    main()