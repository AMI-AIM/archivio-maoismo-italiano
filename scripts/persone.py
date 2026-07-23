import pandas as pd
import os
import re
from collections import defaultdict
from core.utils import slugify, formatta_data, split_nomi

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'docs')

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
                'documenti': documenti
            }
    
    if not persone:
        print("   ⚠️ Nessuna persona ha documenti associati nel catalogo.")
        return
    
    print(f"   📊 Trovate {len(persone)} persone con documenti associati.")
    
    persone_dir = os.path.join(OUTPUT_DIR, 'persone')
    os.makedirs(persone_dir, exist_ok=True)
    
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
    margin: 0.5rem 0 1rem 0;
    color: var(--md-primary-fg-color);
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
    color: var(--md-primary-fg-color);
    background: var(--md-primary-fg-color--light);
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
}
</style>
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter + content)
        
        print(f"   ✅ Creata scheda per {nome} → {slug}.md")
    
    index_content = """---
title: "Persone"
hide:
  - navigation
  - toc
---

# Persone

<div class="people-grid">
"""
    
    for nome in sorted(persone.keys()):
        slug = persone[nome]['slug']
        num_doc = len(persone[nome]['documenti'])
        count_text = f"{num_doc} documento" if num_doc == 1 else f"{num_doc} documenti"
        
        index_content += f"""
<div class="people-card">
    <a href="{slug}/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">{nome}</div>
        <div class="people-count">{count_text}</div>
    </a>
</div>
"""
    
    index_content += """
</div>

<style>
.people-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin: 1.5rem 0;
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
    gap: 0.2rem;
}

.people-tipo {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--md-primary-fg-color);
    background: var(--md-primary-fg-color--light);
    padding: 0.1rem 0.6rem;
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

.people-count {
    font-size: 0.75rem;
    color: var(--md-default-fg-color--light);
    margin-top: 0.2rem;
}

@media (max-width: 900px) {
    .people-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 600px) {
    .people-grid {
        grid-template-columns: 1fr;
    }
    .people-name {
        font-size: 0.9rem;
    }
}
</style>
"""
    
    index_path = os.path.join(persone_dir, 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"   ✅ Indice persone generato con {len(persone)} persone.")

def main():
    print("🚀 Avvio del generatore di schede persone...")
    genera_persone()

if __name__ == "__main__":
    main()