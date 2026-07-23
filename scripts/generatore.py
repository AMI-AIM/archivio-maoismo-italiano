import pandas as pd
import os
import re
import json
from datetime import datetime

# ============================================================
# PERCORSI
# ============================================================

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'docs')

# ============================================================
# FUNZIONI DI SUPPORTO
# ============================================================

def slugify(name):
    if not name or name in ['nan', 'None']:
        return ''
    name = name.lower()
    name = re.sub(r'[àáâãäå]', 'a', name)
    name = re.sub(r'[èéêë]', 'e', name)
    name = re.sub(r'[ìíîï]', 'i', name)
    name = re.sub(r'[òóôõö]', 'o', name)
    name = re.sub(r'[ùúûü]', 'u', name)
    name = re.sub(r'[()\.]', ' ', name)
    name = re.sub(r'[^a-z0-9\s-]', '', name)
    name = re.sub(r'\s+', '-', name)
    name = re.sub(r'-+', '-', name)
    return name.strip('-')

def formatta_data(data_str):
    if not data_str or data_str in ['nan', 'None', 'n.d.']:
        return 'n.d.', (9999, 1, 1)
    
    data_str = str(data_str).strip()
    
    if re.match(r'^\d{4}$', data_str):
        return data_str, (int(data_str), 1, 1)
    
    try:
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y', '%m/%d/%Y']:
            try:
                dt = datetime.strptime(data_str, fmt)
                mesi = {1: 'gennaio', 2: 'febbraio', 3: 'marzo', 4: 'aprile',
                        5: 'maggio', 6: 'giugno', 7: 'luglio', 8: 'agosto',
                        9: 'settembre', 10: 'ottobre', 11: 'novembre', 12: 'dicembre'}
                if fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y', '%m/%d/%Y']:
                    return f"{dt.day} {mesi[dt.month]} {dt.year}", (dt.year, dt.month, dt.day)
                else:
                    return f"{mesi[dt.month]} {dt.year}", (dt.year, dt.month, 1)
            except ValueError:
                continue
    except:
        pass
    
    try:
        if isinstance(data_str, (int, float)):
            dt = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(data_str) - 2)
            mesi = {1: 'gennaio', 2: 'febbraio', 3: 'marzo', 4: 'aprile',
                    5: 'maggio', 6: 'giugno', 7: 'luglio', 8: 'agosto',
                    9: 'settembre', 10: 'ottobre', 11: 'novembre', 12: 'dicembre'}
            return f"{dt.day} {mesi[dt.month]} {dt.year}", (dt.year, dt.month, dt.day)
    except:
        pass
    
    return data_str, (9999, 1, 1)

def split_nomi(nomi_str):
    if not nomi_str or nomi_str in ['nan', 'None']:
        return []
    return [n.strip() for n in re.split(r'[;,]+', nomi_str) if n.strip()]

def carica_soggetti():
    persone = {}
    organizzazioni = {}
    
    try:
        persone_path = os.path.join(DATA_DIR, 'persone.xlsx')
        df_persone = pd.read_excel(persone_path, dtype=str).fillna('')
        df_persone.columns = df_persone.columns.str.strip().str.lower()
        for _, row in df_persone.iterrows():
            nome = str(row.get('nome', '')).strip()
            if nome and nome not in ['nan', 'None']:
                persone[nome] = {
                    'slug': slugify(nome),
                    'biografia': str(row.get('biografia', '')).strip(),
                    'nascita': str(row.get('nascita', '')).strip(),
                    'morte': str(row.get('morte', '')).strip()
                }
        print(f"   ✅ Caricate {len(persone)} persone da data/persone.xlsx")
    except FileNotFoundError:
        print("   ⚠️ File data/persone.xlsx non trovato. Le persone non saranno linkate.")
    except Exception as e:
        print(f"   ⚠️ Errore durante il caricamento di data/persone.xlsx: {e}")
    
    try:
        org_path = os.path.join(DATA_DIR, 'organizzazioni.xlsx')
        df_org = pd.read_excel(org_path, dtype=str).fillna('')
        df_org.columns = df_org.columns.str.strip().str.lower()
        for _, row in df_org.iterrows():
            nome = str(row.get('nome', '')).strip()
            if nome and nome not in ['nan', 'None']:
                organizzazioni[nome] = {
                    'slug': slugify(nome),
                    'storia': str(row.get('storia', '')).strip(),
                    'categoria': str(row.get('categoria', '')).strip(),
                    'fondazione': str(row.get('fondazione', '')).strip()
                }
        print(f"   ✅ Caricate {len(organizzazioni)} organizzazioni da data/organizzazioni.xlsx")
    except FileNotFoundError:
        print("   ⚠️ File data/organizzazioni.xlsx non trovato. Le organizzazioni non saranno linkate.")
    except Exception as e:
        print(f"   ⚠️ Errore durante il caricamento di data/organizzazioni.xlsx: {e}")
    
    return persone, organizzazioni

def trova_soggetto(nome, persone, organizzazioni):
    if not nome or nome in ['nan', 'None']:
        return None, None
    
    if nome in persone:
        return 'persone', persone[nome]['slug']
    elif nome in organizzazioni:
        return 'organizzazioni', organizzazioni[nome]['slug']
    else:
        return None, None

def crea_link(nome, persone, organizzazioni):
    if not nome or nome in ['nan', 'None']:
        return ''
    sezione, slug = trova_soggetto(nome, persone, organizzazioni)
    if sezione:
        return f'<a href="/archivio-maoismo-italiano/{sezione}/{slug}/">{nome}</a>'
    else:
        return nome

def link_lista(nomi_str, persone, organizzazioni):
    nomi = split_nomi(nomi_str)
    if not nomi:
        return 'N/A'
    links = []
    for nome in nomi:
        if nome:
            link = crea_link(nome, persone, organizzazioni)
            links.append(link)
    if links:
        return ', '.join(links)
    return 'N/A'

# ============================================================
# SCARICA DESCRIZIONE DA INTERNET ARCHIVE
# ============================================================

def scarica_descrizione_ia(identifier):
    if not identifier:
        return None
    
    try:
        import requests
        url = f"https://archive.org/metadata/{identifier}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            desc = data.get('metadata', {}).get('description', '')
            if desc:
                desc = re.sub(r'<[^>]+>', '', desc)
                desc = desc.strip()
                return desc
    except Exception as e:
        print(f"   ⚠️ Errore scaricando descrizione per {identifier}: {e}")
    
    return None

# ============================================================
# CREAZIONE SCHEDE DOCUMENTI
# ============================================================

def crea_schede(df, persone, organizzazioni):
    print("📄 Creazione delle schede dei documenti...")
    
    documenti_dir = os.path.join(OUTPUT_DIR, 'documenti')
    os.makedirs(documenti_dir, exist_ok=True)
    contatore = 0
    
    for index, row in df.iterrows():
        ami_id = str(row.get('id', '')).strip()
        if not ami_id or pd.isna(row.get('id')):
            continue
        
        titolo = str(row.get('titolo', 'Senza titolo')).strip()
        if titolo in ['nan', 'None', '']:
            titolo = 'Senza titolo'
        
        autore_raw = str(row.get('autore', '')).strip()
        if autore_raw in ['nan', 'None']:
            autore_raw = ''
        
        org_raw = str(row.get('organizzazione', '')).strip()
        if org_raw in ['nan', 'None']:
            org_raw = ''
        
        persone_collegate = str(row.get('persone_collegate', '')).strip()
        if persone_collegate in ['nan', 'None']:
            persone_collegate = ''
        
        organizzazioni_collegate = str(row.get('organizzazioni_collegate', '')).strip()
        if organizzazioni_collegate in ['nan', 'None']:
            organizzazioni_collegate = ''
        
        data_raw = str(row.get('data', row.get('anno', ''))).strip()
        if data_raw in ['nan', 'None', '']:
            data_raw = ''
        data_formattata, _ = formatta_data(data_raw)
        
        tipo = str(row.get('tipo', '')).strip()
        if tipo in ['nan', 'None']:
            tipo = ''
        if tipo.lower() == 'fotografia':
            tipo = 'foto'
        
        serie = str(row.get('serie', '')).strip()
        if serie in ['nan', 'None']:
            serie = ''
        
        keywords = str(row.get('keywords', '')).strip()
        if keywords in ['nan', 'None']:
            keywords = ''
        
        url_ia = str(row.get('url', '#')).strip()
        if url_ia in ['nan', 'None', '']:
            url_ia = '#'
        
        nome_file = str(row.get('nome_file', '')).strip()
        if nome_file in ['nan', 'None']:
            nome_file = ''
        
        identifier = None
        if url_ia and url_ia != '#':
            match = re.search(r'/details/([^/?#]+)', url_ia)
            if match:
                identifier = match.group(1)
        
        descrizione_ia = scarica_descrizione_ia(identifier) if identifier else None
        
        autore_links = []
        if autore_raw and autore_raw not in ['nan', 'None']:
            autori = split_nomi(autore_raw)
            for autore in autori:
                link = crea_link(autore, persone, organizzazioni)
                autore_links.append(link)
        autore_html = ', '.join(autore_links) if autore_links else 'N/A'
        
        org_html = link_lista(org_raw, persone, organizzazioni)
        persone_collegate_html = link_lista(persone_collegate, persone, organizzazioni)
        organizzazioni_collegate_html = link_lista(organizzazioni_collegate, persone, organizzazioni)
        
        frontmatter = f"""---
title: "{titolo}"
ami_id: {ami_id}
organization: "{org_raw}"
author: "{autore_raw}"
year: "{data_formattata}"
type: "{tipo}"
series: "{serie}"
keywords: "{keywords}"
description: "{tipo} su {org_raw} - Documento conservato su Internet Archive."
hide:
  - navigation
  - toc
---
"""
        
        content = f"""
<div class="doc-date-large">{data_formattata if data_formattata else 'Data non disponibile'}</div>
<h1 class="doc-title-large">{titolo}</h1>

<div class="embed-container">
"""

        if tipo.lower() == 'foto' and identifier:
            if nome_file:
                img_url = f"https://archive.org/download/{identifier}/{nome_file}"
            else:
                img_url = f"https://archive.org/download/{identifier}/{identifier}.jpg"
            
            content += f"""
    <div class="photo-viewer">
        <img src="{img_url}" 
             alt="{titolo}" 
             class="photo-embed"
             onerror="this.style.display='none'; this.parentElement.querySelector('.photo-fallback').style.display='block';">
        <div class="photo-fallback" style="display:none; padding:1rem; text-align:center;">
            <p>🔗 <a href="{url_ia}" target="_blank">Visualizza la foto su Internet Archive</a></p>
        </div>
        <div class="embed-footer">
            <a href="{url_ia}" target="_blank">🔗 Apri su Internet Archive</a>
        </div>
    </div>
"""
        elif identifier:
            if tipo.lower() == 'audio':
                embed_url = f"https://archive.org/embed/{identifier}"
            else:
                embed_url = f"https://archive.org/embed/{identifier}?ui=embed&nav=0"
            
            content += f"""
    <iframe src="{embed_url}" 
            class="universal-embed" 
            allowfullscreen>
    </iframe>
    <div class="embed-footer">
        <a href="{url_ia}" target="_blank">🔗 Apri su Internet Archive</a>
    </div>
"""
        else:
            content += f"""
    <div class="no-embed">
        <p>📄 <a href="{url_ia}" target="_blank">Visualizza il documento su Internet Archive</a></p>
    </div>
"""

        content += f"""
</div>
"""

        # 🔥 DESCRIZIONE SOTTO IL VISUALIZZATORE
        if descrizione_ia:
            content += f"""
<div class="doc-abstract">
    <p>{descrizione_ia}</p>
</div>
"""

        content += f"""
<div class="doc-metadata">
    <div class="metadata-grid">
        <div class="metadata-item">
            <span class="metadata-label">Autore</span>
            <span class="metadata-value">{autore_html}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Organizzazione</span>
            <span class="metadata-value">{org_html}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Persone collegate</span>
            <span class="metadata-value">{persone_collegate_html}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Organizzazioni collegate</span>
            <span class="metadata-value">{organizzazioni_collegate_html}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Data</span>
            <span class="metadata-value">{data_formattata if data_formattata else 'N/A'}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Tipologia</span>
            <span class="metadata-value">{tipo if tipo else 'N/A'}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Serie</span>
            <span class="metadata-value">{serie if serie else 'N/A'}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Parole chiave</span>
            <span class="metadata-value">{keywords if keywords else 'N/A'}</span>
        </div>
    </div>
</div>

<style>
.doc-date-large {{
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--md-primary-fg-color);
    margin: 0.5rem 0 0 0;
    line-height: 1.2;
    letter-spacing: -0.02em;
}}

.doc-title-large {{
    font-size: 2.4rem;
    font-weight: 700;
    margin: 0.2rem 0 1.5rem 0;
    line-height: 1.2;
    letter-spacing: -0.02em;
    color: var(--md-default-fg-color);
}}

.embed-container {{
    margin: 1.5rem 0;
    background: var(--md-code-bg-color);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    min-height: 100px;
}}

.universal-embed {{
    width: 100%;
    height: 600px;
    border: none;
    display: block;
    background: var(--md-code-bg-color);
}}

.photo-viewer {{
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1rem;
    background: var(--md-code-bg-color);
}}

.photo-embed {{
    max-width: 100%;
    max-height: 80vh;
    object-fit: contain;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

.photo-fallback {{
    padding: 2rem;
    text-align: center;
    color: var(--md-default-fg-color--light);
}}

.photo-fallback a {{
    color: var(--md-primary-fg-color);
    text-decoration: none;
    font-weight: 500;
}}

.photo-fallback a:hover {{
    text-decoration: underline;
}}

.embed-footer {{
    padding: 0.5rem 1rem 0.8rem 1rem;
    font-size: 0.9rem;
    text-align: right;
    background: var(--md-code-bg-color);
    border-top: 1px solid var(--md-default-fg-color--lightest);
}}

.embed-footer a {{
    color: var(--md-primary-fg-color);
    text-decoration: none;
    font-weight: 500;
}}

.embed-footer a:hover {{
    text-decoration: underline;
}}

.no-embed {{
    padding: 2rem;
    text-align: center;
    color: var(--md-default-fg-color--light);
}}

.doc-abstract {{
    margin: 1.5rem 0;
    padding: 1rem 1.5rem;
    background: var(--md-code-bg-color);
    border-left: 4px solid var(--md-primary-fg-color);
    border-radius: 4px;
    font-size: 0.95rem;
    line-height: 1.6;
    color: var(--md-default-fg-color--light);
}}

.doc-abstract p {{
    margin: 0;
}}

.doc-metadata {{
    margin-top: 2.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--md-default-fg-color--lightest);
}}

.metadata-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 0.8rem 2rem;
}}

.metadata-item {{
    display: flex;
    flex-direction: column;
    padding: 0.3rem 0;
}}

.metadata-label {{
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--md-default-fg-color--light);
    margin-bottom: 0.1rem;
}}

.metadata-value {{
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--md-default-fg-color);
    word-break: break-word;
}}

.metadata-value a {{
    color: var(--md-primary-fg-color);
    text-decoration: none;
}}

.metadata-value a:hover {{
    text-decoration: underline;
}}

@media (max-width: 600px) {{
    .doc-date-large {{
        font-size: 1.3rem;
    }}
    .doc-title-large {{
        font-size: 1.6rem;
    }}
    .universal-embed {{
        height: 400px;
    }}
    .photo-embed {{
        max-height: 50vh;
    }}
    .photo-viewer {{
        padding: 0.5rem;
    }}
    .doc-abstract {{
        padding: 0.8rem 1rem;
        font-size: 0.85rem;
        margin: 1rem 0;
    }}
    .metadata-grid {{
        grid-template-columns: 1fr;
        gap: 0.3rem;
    }}
    .metadata-item {{
        flex-direction: row;
        gap: 0.5rem;
        padding: 0.2rem 0;
        border-bottom: 1px solid var(--md-default-fg-color--lightest);
    }}
    .metadata-label {{
        min-width: 100px;
        font-size: 0.7rem;
    }}
    .metadata-value {{
        font-size: 0.85rem;
    }}
}}
</style>
"""
        
        file_path = os.path.join(documenti_dir, f'{ami_id}.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter + content)
        
        contatore += 1
        print(f"   ✅ Creata scheda per {ami_id} (tipo: {tipo})")
    
    return contatore

# ============================================================
# GENERAZIONE INDICE ARCHIVIO
# ============================================================

def genera_indice(df):
    print("\n📑 Generazione della pagina Archivio con filtri...")
    
    schede = []
    anni_valori = []
    
    for index, row in df.iterrows():
        ami_id = str(row.get('id', '')).strip()
        if not ami_id:
            continue
        
        titolo = str(row.get('titolo', 'Senza titolo')).strip()
        if titolo in ['nan', 'None', '']:
            titolo = 'Senza titolo'
        
        data_raw = str(row.get('data', row.get('anno', ''))).strip()
        if data_raw in ['nan', 'None', '']:
            data_raw = 'n.d.'
        data_formattata, data_ordine = formatta_data(data_raw)
        
        tipo = str(row.get('tipo', '')).strip()
        if tipo in ['nan', 'None']:
            tipo = ''
        org = str(row.get('organizzazione', '')).strip()
        if org in ['nan', 'None']:
            org = ''
        autore_raw = str(row.get('autore', '')).strip()
        if autore_raw in ['nan', 'None']:
            autore_raw = ''
        keywords = str(row.get('keywords', '')).strip()
        if keywords in ['nan', 'None']:
            keywords = ''
        
        # 🔥 DESCRIZIONE DA IA
        url_ia = str(row.get('url', '#')).strip()
        descrizione = None
        if url_ia and url_ia != '#':
            match = re.search(r'/details/([^/?#]+)', url_ia)
            if match:
                identifier = match.group(1)
                descrizione = scarica_descrizione_ia(identifier)
        
        # 🔥 AUTORE LEGGIBILE (primo autore se multiplo)
        if autore_raw and autore_raw not in ['nan', 'None']:
            autori = split_nomi(autore_raw)
            autore_display = autori[0] if autori else 'N/A'
        else:
            autore_display = 'N/A'
        
        if data_ordine[0] != 9999:
            anni_valori.append(data_ordine[0])
        
        schede.append({
            'id': ami_id,
            'titolo': titolo,
            'data': data_formattata,
            'data_ordine': data_ordine,
            'tipo': tipo,
            'organizzazione': org,
            'autore': autore_display,
            'descrizione': descrizione
        })
    
    schede.sort(key=lambda x: (x['data_ordine'], x['titolo']))
    
    anno_min = min(anni_valori) if anni_valori else 1900
    anno_max = max(anni_valori) if anni_valori else 2025
    
    # 🔥 COSTRUISCI I RISULTATI PRIMA DI SCRIVERE IL FILE
    risultati_html = ""
    for s in schede:
        meta_parts = []
        if s['autore'] and s['autore'] != 'N/A':
            meta_parts.append(s['autore'])
        if s['organizzazione'] and s['organizzazione'] not in ['nan', 'None', '']:
            meta_parts.append(s['organizzazione'])
        if s['tipo'] and s['tipo'] not in ['nan', 'None', '']:
            meta_parts.append(s['tipo'])
        meta_line = ' · '.join(meta_parts) if meta_parts else 'N/A'
        
        risultati_html += f"""
<div class="risultato-card">
    <div class="risultato-data">{s['data']}</div>
    <div class="risultato-contenuto">
        <div class="risultato-titolo">
            <a href="{s['id']}/">{s['titolo']}</a>
        </div>
        <div class="risultato-meta">{meta_line}</div>
        {f'<div class="risultato-desc">{s["descrizione"]}</div>' if s.get("descrizione") else ''}
    </div>
</div>"""
    
    # 🔥 COSTRUISCI L'INTERO CONTENUTO CON I RISULTATI INCLUSI
    index_content = f"""---
title: "Archivio"
hide:
  - navigation
  - toc
---

# Archivio

<div id="archivio-container" class="archivio-layout">

    <!-- SIDEBAR FILTRI -->
    <aside class="filtri-sidebar" id="filtri-sidebar">
        <h4>Filtri</h4>
        
        <div class="filtro-gruppo collapsible">
            <button class="filtro-toggle" id="toggle-organizzazione">
                <span>Organizzazione</span>
                <span class="toggle-icon">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-organizzazione-container">
                <select id="filtro-organizzazione" multiple>
                    <option value="all">Tutte</option>
                </select>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button class="filtro-toggle" id="toggle-persona">
                <span>Persona</span>
                <span class="toggle-icon">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-persona-container">
                <select id="filtro-persona" multiple>
                    <option value="all">Tutte</option>
                </select>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button class="filtro-toggle" id="toggle-tipo">
                <span>Tipologia</span>
                <span class="toggle-icon">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-tipo-container">
                <select id="filtro-tipo" multiple>
                    <option value="all">Tutte</option>
                </select>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button class="filtro-toggle" id="toggle-anno">
                <span>Anno</span>
                <span class="toggle-icon">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-anno-container">
                <div class="slider-container" id="slider-container">
                    <div class="slider-track">
                        <div class="slider-track-fill" id="slider-track-fill"></div>
                    </div>
                    <input type="range" id="filtro-anno-min" min="{anno_min}" max="{anno_max}" value="{anno_min}">
                    <input type="range" id="filtro-anno-max" min="{anno_min}" max="{anno_max}" value="{anno_max}">
                    <div class="slider-labels">
                        <span id="anno-min-label">{anno_min}</span>
                        <span id="anno-max-label">{anno_max}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="filtro-gruppo">
            <label for="filtro-testo">Cerca nel testo</label>
            <input type="text" id="filtro-testo" placeholder="Cerca titolo, autore, keywords...">
        </div>
        
        <div class="filtri-azioni">
            <button id="reset-filtri">↺ Reset</button>
            <span id="risultati-conteggio"></span>
        </div>
    </aside>

    <!-- RISULTATI -->
    <main class="risultati-main">
        <div id="risultati-container">
            {risultati_html if risultati_html else '<p class="loading">Nessun documento trovato.</p>'}
        </div>
    </main>

</div>

<script src="/archivio-maoismo-italiano/archivio-filtri.js"></script>

<style>
.archivio-layout {{
    display: flex;
    gap: 2rem;
    align-items: flex-start;
    margin-top: 1rem;
}}

.filtri-sidebar {{
    flex: 0 0 260px;
    background: var(--md-code-bg-color);
    padding: 1.2rem 1.2rem 1.5rem 1.2rem;
    border-radius: 8px;
    border: 1px solid var(--md-default-fg-color--lightest);
    position: sticky;
    top: 1.5rem;
    max-height: 90vh;
    overflow-y: auto;
}}

.filtri-sidebar h4 {{
    margin: 0 0 1rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--md-default-fg-color);
    border-bottom: 1px solid var(--md-default-fg-color--lightest);
    padding-bottom: 0.5rem;
}}

.filtro-gruppo {{
    margin-bottom: 0.5rem;
    border-bottom: 1px solid var(--md-default-fg-color--lightest);
}}

.filtro-toggle {{
    background: none;
    border: none;
    padding: 0.5rem 0;
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--md-default-fg-color);
    cursor: pointer;
    transition: color 0.15s;
}}

.filtro-toggle:hover {{
    color: var(--md-primary-fg-color);
}}

.filtro-toggle .toggle-icon {{
    font-size: 0.6rem;
    transition: transform 0.25s ease;
}}

.filtro-toggle.open .toggle-icon {{
    transform: rotate(180deg);
}}

.filtro-contenuto {{
    padding: 0.2rem 0 0.8rem 0;
    display: none;
}}

.filtro-contenuto.open {{
    display: block;
}}

.filtro-gruppo label {{
    display: block;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--md-default-fg-color--light);
    margin-bottom: 0.2rem;
}}

.filtro-gruppo select,
.filtro-gruppo input[type="text"] {{
    width: 100%;
    padding: 0.3rem 0.5rem;
    border: 1px solid var(--md-default-fg-color--lightest);
    border-radius: 4px;
    background: var(--md-default-bg-color);
    color: var(--md-default-fg-color);
    font-size: 0.85rem;
}}

.filtro-gruppo select[multiple] {{
    height: auto;
    min-height: 60px;
}}

.filtro-gruppo select[multiple] option {{
    padding: 0.15rem 0.3rem;
}}

.filtro-gruppo select[multiple] option:checked {{
    background: var(--md-primary-fg-color);
    color: var(--md-primary-bg-color);
}}

.slider-container {{
    position: relative;
    width: 100%;
    height: 36px;
    margin: 0.5rem 0;
}}

.slider-track {{
    position: absolute;
    width: 100%;
    height: 4px;
    top: 50%;
    transform: translateY(-50%);
    background: var(--md-default-fg-color--lightest);
    border-radius: 2px;
}}

.slider-track-fill {{
    position: absolute;
    height: 100%;
    background: var(--md-primary-fg-color);
    border-radius: 2px;
    left: 0%;
    right: 0%;
}}

.slider-container input[type="range"] {{
    position: absolute;
    width: 100%;
    top: 0;
    left: 0;
    height: 100%;
    -webkit-appearance: none;
    appearance: none;
    background: transparent;
    pointer-events: none;
    margin: 0;
    padding: 0;
}}

.slider-container input[type="range"]::-webkit-slider-thumb {{
    -webkit-appearance: none;
    appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--md-primary-fg-color);
    cursor: pointer;
    pointer-events: auto;
    border: 2px solid var(--md-default-bg-color);
    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
    z-index: 2;
    margin-top: -6px;
}}

.slider-container input[type="range"]::-moz-range-thumb {{
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--md-primary-fg-color);
    cursor: pointer;
    pointer-events: auto;
    border: 2px solid var(--md-default-bg-color);
    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
    z-index: 2;
}}

.slider-container input[type="range"]::-webkit-slider-runnable-track {{
    height: 4px;
    background: transparent;
    border-radius: 2px;
}}

.slider-container input[type="range"]::-moz-range-track {{
    height: 4px;
    background: transparent;
    border-radius: 2px;
}}

.slider-labels {{
    display: flex;
    justify-content: space-between;
    margin-top: 0.8rem;
    font-size: 0.75rem;
    color: var(--md-default-fg-color--light);
}}

.slider-labels span {{
    background: var(--md-code-bg-color);
    padding: 0.05rem 0.5rem;
    border-radius: 4px;
    font-weight: 500;
}}

.filtri-azioni {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.8rem;
    flex-wrap: wrap;
    gap: 0.3rem;
    border-top: 1px solid var(--md-default-fg-color--lightest);
    padding-top: 0.8rem;
}}

#reset-filtri {{
    padding: 0.2rem 0.8rem;
    background: var(--md-default-fg-color--lightest);
    border: none;
    border-radius: 4px;
    color: var(--md-default-fg-color);
    font-size: 0.75rem;
    cursor: pointer;
    transition: background 0.15s;
}}

#reset-filtri:hover {{
    background: var(--md-default-fg-color--lighter);
}}

#risultati-conteggio {{
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--md-primary-fg-color);
}}

.risultati-main {{
    flex: 1;
    min-width: 0;
}}

.risultato-card {{
    display: flex;
    flex-direction: column;
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid var(--md-default-fg-color--lightest);
    transition: background 0.15s;
}}

.risultato-card:hover {{
    background: var(--md-code-bg-color);
}}

.risultato-data {{
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--md-primary-fg-color);
}}

.risultato-titolo {{
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0.1rem 0;
}}

.risultato-titolo a {{
    text-decoration: none;
    color: var(--md-default-fg-color);
}}

.risultato-titolo a:hover {{
    text-decoration: underline;
    color: var(--md-primary-fg-color);
}}

.risultato-meta {{
    font-size: 0.85rem;
    color: var(--md-default-fg-color--light);
    margin: 0.1rem 0;
}}

.risultato-meta .separator {{
    margin: 0 0.3rem;
    color: var(--md-default-fg-color--lightest);
}}

.risultato-desc {{
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 0.9rem;
    color: var(--md-default-fg-color--light);
    line-height: 1.5;
    max-height: 4.5em;
    margin: 0.1rem 0 0 0;
}}

.nessun-risultato {{
    text-align: center;
    padding: 2rem;
    color: var(--md-default-fg-color--light);
}}

.loading {{
    text-align: center;
    padding: 2rem;
    color: var(--md-default-fg-color--light);
}}

@media (max-width: 768px) {{
    .archivio-layout {{
        flex-direction: column;
    }}
    .filtri-sidebar {{
        flex: 0 0 auto;
        position: static;
        max-height: none;
        width: 100%;
    }}
    .risultato-card {{
        padding: 0.6rem 0.4rem;
    }}
    .risultato-titolo {{
        font-size: 1rem;
    }}
    .risultato-meta {{
        font-size: 0.8rem;
    }}
    .risultato-desc {{
        font-size: 0.85rem;
    }}
}}
</style>
"""
    
    # 🔥 SCRIVI IL FILE CON TUTTO IL CONTENUTO
    index_path = os.path.join(OUTPUT_DIR, 'documenti', 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"   ✅ Pagina Archivio generata con {len(schede)} schede.")
    print(f"   📅 Intervallo anni: {anno_min} - {anno_max}")


# ============================================================
# GENERAZIONE JSON PER I FILTRI
# ============================================================

def genera_json(df, persone, organizzazioni):
    print("\n📊 Generazione del file JSON per i filtri...")
    
    documenti_json = []
    anni_valori = []
    
    for index, row in df.iterrows():
        ami_id = str(row.get('id', '')).strip()
        if not ami_id or pd.isna(row.get('id')):
            continue
        
        titolo = str(row.get('titolo', 'Senza titolo')).strip()
        if titolo in ['nan', 'None', '']:
            titolo = 'Senza titolo'
        
        autore_raw = str(row.get('autore', '')).strip()
        if autore_raw in ['nan', 'None']:
            autore_raw = ''
        
        org_raw = str(row.get('organizzazione', '')).strip()
        if org_raw in ['nan', 'None']:
            org_raw = ''
        
        persone_collegate = str(row.get('persone_collegate', '')).strip()
        if persone_collegate in ['nan', 'None']:
            persone_collegate = ''
        
        organizzazioni_collegate = str(row.get('organizzazioni_collegate', '')).strip()
        if organizzazioni_collegate in ['nan', 'None']:
            organizzazioni_collegate = ''
        
        data_raw = str(row.get('data', row.get('anno', ''))).strip()
        if data_raw in ['nan', 'None', '']:
            data_raw = ''
        data_formattata, data_ordine = formatta_data(data_raw)
        
        tipo = str(row.get('tipo', '')).strip()
        if tipo in ['nan', 'None']:
            tipo = ''
        if tipo.lower() == 'fotografia':
            tipo = 'foto'
        
        serie = str(row.get('serie', '')).strip()
        if serie in ['nan', 'None']:
            serie = ''
        
        keywords = str(row.get('keywords', '')).strip()
        if keywords in ['nan', 'None']:
            keywords = ''
        
        url_ia = str(row.get('url', '#')).strip()
        if url_ia in ['nan', 'None', '']:
            url_ia = '#'
        
        anno = None
        if data_ordine and data_ordine[0] != 9999:
            anno = data_ordine[0]
            anni_valori.append(anno)
        elif data_raw and data_raw.isdigit():
            anno = int(data_raw)
            anni_valori.append(anno)
        
        # PERSONE: SOLO quelle che sono in persone.xlsx
        persone_lista = []
        if autore_raw and autore_raw not in ['nan', 'None']:
            autori = split_nomi(autore_raw)
            for autore in autori:
                if autore in persone:
                    persone_lista.append(autore)
        if persone_collegate and persone_collegate not in ['nan', 'None']:
            collegati = split_nomi(persone_collegate)
            for collegato in collegati:
                if collegato in persone:
                    persone_lista.append(collegato)
        persone_lista = list(set(persone_lista))
        
        # ORGANIZZAZIONI: SOLO quelle che sono in organizzazioni.xlsx
        organizzazioni_lista = []
        if org_raw and org_raw not in ['nan', 'None']:
            orgs = split_nomi(org_raw)
            for org in orgs:
                if org in organizzazioni:
                    organizzazioni_lista.append(org)
        if organizzazioni_collegate and organizzazioni_collegate not in ['nan', 'None']:
            collegati = split_nomi(organizzazioni_collegate)
            for collegato in collegati:
                if collegato in organizzazioni:
                    organizzazioni_lista.append(collegato)
        if autore_raw and autore_raw not in ['nan', 'None']:
            autori = split_nomi(autore_raw)
            for autore in autori:
                if autore in organizzazioni:
                    organizzazioni_lista.append(autore)
        organizzazioni_lista = list(set(organizzazioni_lista))
        
        doc_obj = {
            'id': ami_id,
            'titolo': titolo,
            'autore': autore_raw,
            'organizzazione': org_raw,
            'data': data_formattata,
            'anno': anno,
            'tipo': tipo,
            'serie': serie,
            'keywords': keywords,
            'url_ia': url_ia,
            'persone': persone_lista,
            'organizzazioni': organizzazioni_lista
        }
        documenti_json.append(doc_obj)
    
    documenti_json.sort(key=lambda x: (x['anno'] is None, x['anno'] if x['anno'] else 9999, x['titolo']))
    
    json_data = {
        'documenti': documenti_json,
        'anno_min': min(anni_valori) if anni_valori else 1900,
        'anno_max': max(anni_valori) if anni_valori else 2025
    }
    
    json_path = os.path.join(OUTPUT_DIR, 'documenti.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ JSON generato con {len(documenti_json)} documenti")
    print(f"   📅 Intervallo anni: {json_data['anno_min']} - {json_data['anno_max']}")

# ============================================================
# GENERAZIONE HOME
# ============================================================

def genera_home(df):
    print("\n🏠 Generazione della Home page...")
    
    schede = []
    
    for index, row in df.iterrows():
        ami_id = str(row.get('id', '')).strip()
        if not ami_id:
            continue
        
        titolo = str(row.get('titolo', 'Senza titolo')).strip()
        if titolo in ['nan', 'None', '']:
            titolo = 'Senza titolo'
        
        data_raw = str(row.get('data', row.get('anno', ''))).strip()
        if data_raw in ['nan', 'None', '']:
            data_raw = 'n.d.'
        data_formattata, _ = formatta_data(data_raw)
        
        tipo = str(row.get('tipo', '')).strip()
        if tipo in ['nan', 'None']:
            tipo = ''
        org = str(row.get('organizzazione', '')).strip()
        if org in ['nan', 'None']:
            org = ''
        keywords = str(row.get('keywords', '')).strip()
        if keywords in ['nan', 'None']:
            keywords = ''
        
        parti_sommario = []
        if tipo:
            parti_sommario.append(tipo)
        if org:
            parti_sommario.append(org)
        
        sommario = ' · '.join(parti_sommario) if parti_sommario else 'Documento storico'
        
        try:
            num_id = int(re.search(r'(\d+)', ami_id).group(1))
        except:
            num_id = 0
        
        schede.append({
            'id': ami_id,
            'titolo': titolo,
            'data': data_formattata,
            'sommario': sommario,
            'keywords': keywords,
            'num_id': num_id
        })
    
    schede.sort(key=lambda x: x['num_id'], reverse=True)
    ultime_tre = schede[:3]
    
    home_content = f"""# Archivio del Maoismo Italiano

L'**AMI** è un archivio digitale dedicato alla documentazione storica sul maoismo italiano. Questo sito funge da catalogo scientifico: ogni scheda descrive un documento conservato su **Internet Archive**.

---

## 📥 Aggiunti di recente

<div class="catalogo-lista">

"""
    
    for s in ultime_tre:
        icona = "📄"
        if "opuscolo" in s['sommario'].lower():
            icona = "📘"
        elif "manifesto" in s['sommario'].lower():
            icona = "🖼️"
        elif "foto" in s['sommario'].lower() or "fotografia" in s['sommario'].lower():
            icona = "📷"
        elif "periodico" in s['sommario'].lower():
            icona = "📰"
        elif "volantino" in s['sommario'].lower():
            icona = "📃"
        elif "libro" in s['sommario'].lower():
            icona = "📕"
        elif "audio" in s['sommario'].lower():
            icona = "🎵"
        
        home_content += f"""
<div class="doc-row">
    <div class="doc-data">{icona} {s['data']}</div>
    <div class="doc-contenuto">
        <div class="doc-titolo"><a href="documenti/{s['id']}/">{s['titolo']}</a></div>
        <div class="doc-sommario">{s['sommario']}</div>
        <div class="doc-keywords">{s['keywords'] if s['keywords'] else ''}</div>
    </div>
</div>
"""
    
    home_content += """
</div>

<div style="text-align: center; margin-top: 1.5rem;">
    <a href="documenti/" class="md-button md-button--primary">📂 Tutti i documenti</a>
</div>

<style>
.catalogo-lista {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin-top: 1rem;
}
.doc-row {
    display: flex;
    align-items: flex-start;
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid var(--md-default-fg-color--lightest);
    transition: background-color 0.15s;
    gap: 1.5rem;
}
.doc-row:hover {
    background-color: var(--md-code-bg-color);
}
.doc-data {
    flex: 0 0 180px;
    font-size: 1rem;
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
    font-size: 1.05rem;
    font-weight: 600;
    margin-bottom: 0.1rem;
}
.doc-titolo a {
    text-decoration: none;
    color: var(--md-default-fg-color);
}
.doc-titolo a:hover {
    text-decoration: underline;
    color: var(--md-primary-fg-color);
}
.doc-sommario {
    font-size: 0.9rem;
    color: var(--md-default-fg-color--light);
}
.doc-keywords {
    font-size: 0.8rem;
    color: var(--md-primary-fg-color--light);
    font-style: italic;
}
.md-button {
    display: inline-block;
    padding: 0.6rem 1.5rem;
    border-radius: 0.25rem;
    font-weight: 600;
    text-decoration: none;
    transition: background-color 0.2s;
}
.md-button--primary {
    background-color: var(--md-primary-fg-color);
    color: var(--md-primary-bg-color) !important;
}
.md-button--primary:hover {
    background-color: var(--md-primary-fg-color--dark);
}
@media (max-width: 600px) {
    .doc-row {
        flex-direction: column;
        gap: 0.2rem;
        padding: 0.8rem 0.4rem;
    }
    .doc-data {
        flex: 0 0 auto;
        white-space: normal;
        font-size: 0.9rem;
    }
}
</style>
"""
    
    index_path = os.path.join(OUTPUT_DIR, 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(home_content)
    
    print(f"   ✅ Home generata con {len(ultime_tre)} ultimi documenti.")

# ============================================================
# MAIN
# ============================================================

def main():
    print("🚀 Avvio del generatore di schede AMI...")
    print(f"📂 Root: {ROOT_DIR}")
    print(f"📂 Dati: {DATA_DIR}")
    print(f"📂 Output: {OUTPUT_DIR}")
    
    persone, organizzazioni = carica_soggetti()
    
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
    
    num_schede = crea_schede(df, persone, organizzazioni)
    print(f"\n✅ Create {num_schede} schede in docs/documenti/")
    
    genera_indice(df)
    genera_json(df, persone, organizzazioni)
    genera_home(df)
    
    print("\n🎉 Conversione completata con successo!")

if __name__ == "__main__":
    main()