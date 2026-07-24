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
    
    # 🔥 BANNER CON TAG <img> (larghezza 100%, altezza automatica)
    banner_html = """
<div class="banner-full">
    <img src="/archivio-maoismo-italiano/immagini/banner.png" 
         alt="Archivio del Maoismo Italiano" 
         class="banner-image">
    <div class="banner-overlay"></div>
    <div class="banner-content">
        <p>Documenti, periodici, opuscoli e fonti del movimento marxista-leninista italiano (1960-1992)</p>
        <a href="documenti/" class="banner-button">Esplora l'archivio</a>
    </div>
</div>
"""
    
    home_content = f"""---
hide:
  - toc
---

{banner_html}

## 📥 Aggiunti di recente

<div class="recent-container">

<div class="catalogo-lista">

"""
    
    for s in ultime_tre:
        home_content += f"""
<div class="doc-row">
    <div class="doc-data">{s['data']}</div>
    <div class="doc-contenuto">
        <div class="doc-titolo"><a href="documenti/{s['id']}/">{s['titolo']}</a></div>
        <div class="doc-sommario">{s['sommario']}</div>
        <div class="doc-keywords">{s['keywords'] if s['keywords'] else ''}</div>
    </div>
</div>
"""
    
    home_content += """
</div>
</div>

<div style="text-align: center; margin-top: 1.5rem;">
    <a href="documenti/" class="md-button md-button--primary">📂 Tutti i documenti</a>
</div>

<style>
/* ============================================================
   NASCONDE IL TITOLO "Home" NELLA PAGINA
   ============================================================ */
.md-content article h1:first-of-type {
    display: none !important;
}

/* ============================================================
   CATALOGO
   ============================================================ */
.catalogo-lista {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.doc-row {
    display: flex;
    align-items: flex-start;
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid var(--md-default-fg-color--lightest);
    transition: background-color 0.15s;
    gap: 1.5rem;
}

.doc-row:last-child {
    border-bottom: none;
}

.doc-row:hover {
    background-color: var(--md-code-bg-color);
}

.doc-data {
    flex: 0 0 150px;
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--md-primary-fg-color);
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

.recent-container {
    background: var(--md-code-bg-color);
    border-radius: 12px;
    padding: 0.5rem 0.5rem 0.2rem 0.5rem;
    margin: 1.5rem 0 1rem 0;
    border: 1px solid var(--md-default-fg-color--lightest);
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

/* ============================================================
   BANNER A LARGHEZZA COMPLETA (con img)
   ============================================================ */
.banner-full {
    position: relative;
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
    overflow: hidden;
    margin-top: -2.8rem;       /* Compensa il padding del contenuto */
    margin-bottom: 2rem;
}

.banner-image {
    width: 100%;
    height: auto;
    display: block;
}

.banner-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.45);
}

.banner-content {
    position: absolute;
    z-index: 1;
    text-align: left;
    color: #ffffff;
    padding: 0 2rem;
    max-width: 650px;
    margin-left: 3rem;
    top: 50%;
    transform: translateY(-50%);
}

.banner-content p {
    font-size: 1.2rem;
    opacity: 0.92;
    margin: 0 0 1.5rem 0;
    line-height: 1.5;
    text-shadow: 0 1px 8px rgba(0, 0, 0, 0.2);
    font-weight: 400;
}

.banner-content h1 {
    display: none !important;
}

.banner-button {
    display: inline-block;
    padding: 0.7rem 2.2rem;
    background-color: #ffffff;
    color: #b71c1c !important;
    font-weight: 600;
    font-size: 1rem;
    border-radius: 6px;
    text-decoration: none;
    transition: transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.banner-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

@media (max-width: 768px) {
    .banner-full {
        margin-top: -1.8rem;
        margin-bottom: 1.5rem;
    }
    .banner-content {
        margin-left: 1.5rem;
        padding: 0 1rem;
        max-width: 90%;
    }
    .banner-content p {
        font-size: 1rem;
    }
    .banner-button {
        padding: 0.6rem 1.5rem;
        font-size: 0.9rem;
    }
}

@media (max-width: 480px) {
    .banner-full {
        margin-top: -1.2rem;
    }
    .banner-content p {
        font-size: 0.85rem;
    }
}
</style>
"""
    
    index_path = os.path.join(output_dir, 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(home_content)
    
    print(f"   ✅ Home generata con {len(ultime_tre)} ultimi documenti.")