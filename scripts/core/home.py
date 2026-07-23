import os
import re
from .utils import formatta_data, split_nomi

def genera_home(df, output_dir):
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
    
    immagine_html = """
<div class="home-image-wrapper">
    <img src="/immagini/nuova-unita.png" 
         alt="Prima pagina di Nuova Unità" 
         class="home-image">
</div>
"""
    
    home_content = f"""---
hide:
  - toc
---

# Archivio del Maoismo Italiano

L'**AMI** è un archivio digitale dedicato alla documentazione storica sul maoismo italiano. Questo sito funge da catalogo scientifico: ogni scheda descrive un documento conservato su **Internet Archive**.

{immagine_html}

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
    
    index_path = os.path.join(output_dir, 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(home_content)
    
    print(f"   ✅ Home generata con {len(ultime_tre)} ultimi documenti.")