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
        org_path = os.path.join(DATA_DIR, 'organizzazioni.xlsx')
        df_org = pd.read_excel(org_path, dtype=str).fillna('')
        df_org.columns = df_org.columns.str.strip().str.lower()
    except FileNotFoundError:
        print(f"   ❌ ERRORE: Non trovo '{org_path}'.")
        return
    except Exception as e:
        print(f"   ❌ ERRORE durante la lettura di organizzazioni.xlsx: {e}")
        return
    
    if df_org.empty:
        print("   ⚠️ Il file organizzazioni.xlsx è vuoto.")
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
    
    print(f"   📊 Caricate {len(df_org)} organizzazioni da data/organizzazioni.xlsx")
    print(f"   📊 Caricati {len(df_catalogo)} documenti da data/catalogo.xlsx")
    
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
                data_form, _ = formatta_data(data_raw)
            else:
                data_form = 'n.d.'
            
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
                    'ruoli': ruoli
                })
        
        if documenti:
            documenti.sort(key=lambda x: (x['data'] == 'n.d.', x['data'], x['titolo']))
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
    # GENERA SCHEDE INDIVIDUALI
    # ============================================================
    for nome, data in organizzazioni.items():
        slug = data['slug']
        file_path = os.path.join(org_dir, f'{slug}.md')
        
        storia_text = data['storia']
        if not storia_text:
            storia_text = f'<p><em>Storia in costruzione. Scrivi qui le informazioni su {nome}.</em></p>'
        elif '\n' in storia_text:
            storia_text = '<p>' + '</p><p>'.join(storia_text.split('\n')) + '</p>'
        
        frontmatter = f"""---
title: "{nome}"
description: "Documenti relativi a {nome}"
hide:
  - navigation
  - toc
---
"""
        
        content = f"""
<h1 class="org-name">{nome}</h1>

{f'<div class="org-dates">{data["data_range"]}</div>' if data["data_range"] else ''}

<div class="org-bio">
    {storia_text}
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
.org-name {
    font-size: 2.4rem;
    font-weight: 700;
    margin: 0.5rem 0 0 0;
    color: var(--md-primary-fg-color);
}

.org-dates {
    font-size: 1rem;
    color: var(--md-default-fg-color--light);
    margin: 0 0 1rem 0;
    font-weight: 400;
    letter-spacing: 0.02em;
}

.org-bio {
    margin: 1.5rem 0;
    padding: 1rem;
    background: var(--md-code-bg-color);
    border-radius: 8px;
    border-left: 4px solid var(--md-primary-fg-color);
}

.org-bio p {
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
    .org-name {
        font-size: 1.6rem;
    }
    .org-dates {
        font-size: 0.85rem;
    }
}
</style>
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter + content)
        
        print(f"   ✅ Creata scheda per {nome} → {slug}.md")
    
    # ============================================================
    # INDICE ORGANIZZAZIONI CON TOP 3
    # ============================================================
    
    org_ordinate = sorted(organizzazioni.items(), key=lambda x: x[1]['num_doc'], reverse=True)
    org_top = org_ordinate[:3]
    org_resto = org_ordinate[3:]
    
    index_content = """---
title: "Organizzazioni"
hide:
  - navigation
  - toc
---

# Organizzazioni

"""
    
    if org_top:
        index_content += '<div class="top-row">\n'
        for nome, data in org_top:
            slug = data['slug']
            num_doc = data['num_doc']
            date_range = data['data_range']
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
            <div class="top-card-dates">{date_range}</div>
            <div class="top-card-count">{count_text}</div>
        </a>
    </div>
'''
        index_content += '</div>\n'
    
    if org_resto:
        index_content += '<div class="org-grid">\n'
        for nome, data in org_resto:
            slug = data['slug']
            num_doc = data['num_doc']
            date_range = data['data_range']
            categoria = data['categoria']
            count_text = "1 documento" if num_doc == 1 else f"{num_doc} documenti"
            
            index_content += f'''
<div class="org-card">
    <a href="{slug}/" class="org-link">
        <div class="org-tipo">{categoria}</div>
        <div class="org-name">{nome}</div>
        <div class="org-dates">{date_range}</div>
        <div class="org-count">{count_text}</div>
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

.org-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-top: 1rem;
}

.org-card {
    background: var(--md-code-bg-color);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    transition: background-color 0.2s, transform 0.15s, box-shadow 0.2s;
    border: 1px solid var(--md-default-fg-color--lightest);
    min-height: 100px;
    display: flex;
    align-items: center;
}

.org-card:hover {
    background: var(--md-default-bg-color);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.org-link {
    text-decoration: none;
    display: flex;
    flex-direction: column;
    width: 100%;
    gap: 0.1rem;
}

.org-tipo {
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

.org-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--md-default-fg-color);
    line-height: 1.3;
    word-break: break-word;
}

.org-dates {
    font-size: 0.7rem;
    color: var(--md-default-fg-color--light);
    margin-top: 0.05rem;
}

.org-count {
    font-size: 0.75rem;
    color: var(--md-default-fg-color--light);
    margin-top: 0.1rem;
}

@media (max-width: 900px) {
    .org-grid {
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
    .org-grid {
        grid-template-columns: 1fr;
    }
    .org-name {
        font-size: 0.9rem;
    }
    .org-dates {
        font-size: 0.65rem;
    }
}
</style>
"""
    
    index_path = os.path.join(org_dir, 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"   ✅ Indice organizzazioni generato con {len(organizzazioni)} organizzazioni (top 3 in evidenza).")


def main():
    print("🚀 Avvio del generatore di schede organizzazioni...")
    genera_organizzazioni()


if __name__ == "__main__":
    main()