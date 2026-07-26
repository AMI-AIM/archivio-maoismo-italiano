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
    
    # 🔥 BANNER CON MARGINE NEGATIVO INLINE
    banner_html = """
<div class="banner-full" style="margin-bottom: 2rem;">
    <img src="/archivio-maoismo-italiano/immagini/banner.png" 
         alt="Archivio del Maoismo Italiano" 
         class="banner-image">
    <div class="banner-overlay"></div>
    <div class="banner-content" style="position: absolute; bottom: 0.5rem; left: 0.5rem; z-index: 1; text-align: left; color: #ffffff; max-width: 650px; padding: 0.5rem 1rem;">
        <p style="font-size: 1.2rem; opacity: 0.92; margin: 0 0 0.8rem 0; line-height: 1.5; text-shadow: 0 2px 12px rgba(0,0,0,0.4); font-weight: 400;">Documenti, periodici, opuscoli e fonti del movimento "filo-cinese" in Italia</p>
        <div class="banner-actions" style="display: flex; align-items: center; flex-wrap: nowrap; gap: 0.6rem;">
            <a href="documenti/" class="banner-button" style="display: inline-block; padding: 0.5rem 1.2rem; background-color: #ffffff; color: #b71c1c !important; font-weight: 600; font-size: 0.9rem; border-radius: 6px; text-decoration: none; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 2px 12px rgba(0,0,0,0.25); white-space: nowrap; flex-shrink: 0;">Esplora l'archivio</a>
            <form class="banner-search" id="hero-search-form" action="documenti/" method="get" style="display: flex; align-items: center; gap: 0.4rem; background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.4); border-radius: 24px; padding: 0.3rem 0.8rem; backdrop-filter: blur(2px); transition: background 0.2s, border-color 0.2s; position: relative; flex: 1 1 auto; min-width: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="banner-search-icon" aria-hidden="true" style="width: 1.1rem; height: 1.1rem; fill: #ffffff; flex-shrink: 0;">
                    <path d="M9.5 3A6.5 6.5 0 0 1 16 9.5c0 1.61-.59 3.09-1.56 4.23l.27.27h.79l5 5-1.5 1.5-5-5v-.79l-.27-.27A6.52 6.52 0 0 1 9.5 16 6.5 6.5 0 0 1 3 9.5 6.5 6.5 0 0 1 9.5 3m0 2C7 5 5 7 5 9.5S7 14 9.5 14 14 12 14 9.5 12 5 9.5 5z"/>
                </svg>
                <input type="text" id="hero-search-input" name="q" placeholder="Cerca nell'archivio..." aria-label="Cerca nell'archivio" autocomplete="off" style="background: transparent; border: none; outline: none; color: #ffffff; font-size: 0.9rem; width: 100%; min-width: 140px; flex: 1 1 auto;">
                <button type="submit" aria-label="Cerca" style="background: none; border: none; color: #ffffff; font-weight: 600; font-size: 0.85rem; cursor: pointer; padding: 0.2rem 0.4rem; text-decoration: underline; text-underline-offset: 2px; white-space: nowrap; flex-shrink: 0;">Cerca</button>
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
   BANNER: stili generali (posizionamento e sfondo)
   ============================================================ */
.banner-full {
    position: relative;
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
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

/* Stili per il dropdown dei suggerimenti della ricerca hero */
.hero-search-results {
    display: none;
    max-height: 60vh;
    max-width: 90vw;
    overflow-y: auto;
    background: #ffffff;
    color: #1a1a1a;
    border-radius: 10px;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.3);
    z-index: 9999;
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
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.hero-search-item-tag {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    padding: 0.1rem 0.45rem;
    border-radius: 10px;
    color: #ffffff;
    white-space: nowrap;
}

.hero-search-item-tag--persona {
    background: #6a1b9a;
}

.hero-search-item-tag--organizzazione {
    background: #1565c0;
}

.hero-search-item-tag--documento {
    background: #b71c1c;
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

/* ============================================================
   RESPONSIVE (mobile)
   ============================================================ */
@media (max-width: 768px) {
    .banner-full {
        margin-bottom: 1rem !important;
        height: 240px;
        min-height: 200px;
        overflow: hidden;
    }
    .banner-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center center;
    }
    .banner-content[style] {
        bottom: 0.3rem !important;
        left: 0.3rem !important;
        right: 0.3rem !important;
        max-width: none !important;
        padding: 0.3rem 0.6rem !important;
    }
    .banner-content p[style] {
        font-size: 0.8rem !important;
        margin: 0 0 0.3rem 0 !important;
        line-height: 1.3 !important;
    }
    .banner-actions[style] {
        flex-wrap: wrap !important;
        gap: 0.3rem !important;
    }
    .banner-button[style] {
        padding: 0.3rem 0.8rem !important;
        font-size: 0.75rem !important;
    }
    .banner-search[style] {
        flex: 1 1 100% !important;
        padding: 0.2rem 0.6rem !important;
        gap: 0.3rem !important;
    }
    .banner-search input[style] {
        min-width: 80px !important;
        font-size: 0.75rem !important;
    }
    .banner-search button[style] {
        font-size: 0.7rem !important;
        padding: 0.1rem 0.3rem !important;
    }
    .banner-search-icon[style] {
        width: 0.9rem !important;
        height: 0.9rem !important;
    }
}

@media (max-width: 480px) {
    .banner-full {
        height: 180px;
        min-height: 150px;
    }
    .banner-content p[style] {
        font-size: 0.7rem !important;
    }
    .banner-button[style] {
        padding: 0.2rem 0.6rem !important;
        font-size: 0.65rem !important;
    }
    .banner-search input[style] {
        font-size: 0.7rem !important;
        min-width: 60px !important;
    }
    .banner-search button[style] {
        font-size: 0.65rem !important;
    }
}
</style>
"""
    
    index_path = os.path.join(output_dir, 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(home_content)
    
    print(f"   ✅ Home generata con {len(ultime_tre)} ultimi documenti.")