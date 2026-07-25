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
        <p>Documenti, periodici, opuscoli e fonti del movimento "filo-cinese" in Italia </p>
        <div class="banner-actions">
            <a href="documenti/" class="banner-button">Esplora l'archivio</a>
            <form class="banner-search" id="hero-search-form" action="documenti/" method="get">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="banner-search-icon" aria-hidden="true">
                    <path d="M9.5 3A6.5 6.5 0 0 1 16 9.5c0 1.61-.59 3.09-1.56 4.23l.27.27h.79l5 5-1.5 1.5-5-5v-.79l-.27-.27A6.52 6.52 0 0 1 9.5 16 6.5 6.5 0 0 1 3 9.5 6.5 6.5 0 0 1 9.5 3m0 2C7 5 5 7 5 9.5S7 14 9.5 14 14 12 14 9.5 12 5 9.5 5z"/>
                </svg>
                <input type="text" id="hero-search-input" name="q" placeholder="Cerca nell'archivio..." aria-label="Cerca nell'archivio" autocomplete="off">
                <button type="submit" aria-label="Cerca">Cerca</button>
                <div class="hero-search-results" id="hero-search-results"></div>
            </form>
        </div>
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

/* ============================================================
   BARRA DI RICERCA NELLA HERO
   ============================================================ */
.banner-actions {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}

.banner-search {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.4);
    border-radius: 24px;
    padding: 0.5rem 0.9rem;
    backdrop-filter: blur(2px);
    transition: background 0.2s, border-color 0.2s;
    position: relative;
}

.banner-search:focus-within {
    background: rgba(255, 255, 255, 0.25);
    border-color: rgba(255, 255, 255, 0.7);
}

.banner-search-icon {
    width: 1.1rem;
    height: 1.1rem;
    fill: #ffffff;
    flex-shrink: 0;
}

.banner-search input {
    background: transparent;
    border: none;
    outline: none;
    color: #ffffff;
    font-size: 0.95rem;
    width: 220px;
    max-width: 40vw;
}

.banner-search input::placeholder {
    color: rgba(255, 255, 255, 0.75);
}

.banner-search button {
    background: none;
    border: none;
    color: #ffffff;
    font-weight: 600;
    font-size: 0.85rem;
    cursor: pointer;
    padding: 0.2rem 0.4rem;
    text-decoration: underline;
    text-underline-offset: 2px;
}

.banner-search button:hover {
    color: rgba(255, 255, 255, 0.8);
}

@media (max-width: 768px) {
    .banner-actions {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.8rem;
    }
    .banner-search input {
        width: 60vw;
        max-width: none;
    }
}

/* Dropdown suggerimenti (ricerca istantanea, componente autonomo) */
.hero-search-results {
    display: none;
    position: absolute;
    top: calc(100% + 0.6rem);
    left: 0;
    width: 420px;
    max-width: 90vw;
    max-height: 60vh;
    overflow-y: auto;
    background: #ffffff;
    color: #1a1a1a;
    border-radius: 10px;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.3);
    z-index: 20;
}

.hero-search-results.is-open {
    display: block;
}

.hero-search-count {
    padding: 0.6rem 1rem;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #6b6b6b;
    background: #f5f5f5;
    border-bottom: 1px solid #eaeaea;
}

.hero-search-empty {
    padding: 1rem;
    font-size: 0.9rem;
    color: #6b6b6b;
    text-align: center;
}

.hero-search-item {
    display: block;
    padding: 0.7rem 1rem;
    text-decoration: none;
    border-bottom: 1px solid #f0f0f0;
    color: inherit;
}

.hero-search-item:last-child {
    border-bottom: none;
}

.hero-search-item:hover {
    background: #f7f7f7;
}

.hero-search-item-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 0.15rem;
}

.hero-search-item-snippet {
    font-size: 0.82rem;
    color: #666666;
    line-height: 1.4;
}

.hero-search-item mark,
.hero-search-item-snippet mark {
    background: transparent;
    color: #b71c1c;
    font-weight: 700;
}

@media (max-width: 768px) {
    .hero-search-results {
        width: 100%;
        max-width: none;
    }
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