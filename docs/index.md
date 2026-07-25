---
hide:
  - toc
---


<div class="banner-full">
    <img src="/archivio-maoismo-italiano/immagini/banner.png" 
         alt="Archivio del Maoismo Italiano" 
         class="banner-image">
    <div class="banner-overlay"></div>
    <div class="banner-content" style="position: absolute; bottom: 0.5rem !important; left: 0.5rem !important; z-index: 1; text-align: left; color: #ffffff; max-width: 650px; padding: 0.5rem 1rem;">
        <p style="font-size: 1.2rem; opacity: 0.92; margin: 0 0 0.8rem 0; line-height: 1.5; text-shadow: 0 2px 8px rgba(0,0,0,0.8); font-weight: 400;">Documenti, periodici, opuscoli e fonti del movimento "filo-cinese" in Italia</p>
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


## 📥 Aggiunti di recente

<div class="recent-container">

<div class="catalogo-lista">


<div class="doc-row">
    <div class="doc-data">1970</div>
    <div class="doc-contenuto">
        <div class="doc-titolo"><a href="documenti/AMI-0032/">Statuto di Stella Rossa - Fronte Rivoluzionario Marxista-Leninista</a></div>
        <div class="doc-sommario">Testo · Stella Rossa - Fronte Rivoluzionario Marxista-Leninista</div>
        <div class="doc-keywords">Maoismo; Marxismo-leninismo</div>
    </div>
</div>

<div class="doc-row">
    <div class="doc-data">1968</div>
    <div class="doc-contenuto">
        <div class="doc-titolo"><a href="documenti/AMI-0031/">Sulla tattica contro l'imperialismo giapponese</a></div>
        <div class="doc-sommario">Opuscolo · Casa editrice in lingue estere</div>
        <div class="doc-keywords">Partito comunista cinese; Maoismo; Guerra civile cinese; Lunga marcia</div>
    </div>
</div>

<div class="doc-row">
    <div class="doc-data">1968</div>
    <div class="doc-contenuto">
        <div class="doc-titolo"><a href="documenti/AMI-0030/">La bussola che guida i popoli rivoluzionari di tutti i paesi verso la vittoria</a></div>
        <div class="doc-sommario">Opuscolo · Casa editrice in lingue estere</div>
        <div class="doc-keywords">Partito comunista cinese; Maoismo; Rivoluzione culturale</div>
    </div>
</div>

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
    margin-top: -2.8rem;
    margin-bottom: 2rem;
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
   RESPONSIVE
   ============================================================ */
@media (max-width: 768px) {
    .banner-full {
        margin-top: -1.8rem;
        margin-bottom: 1.5rem;
    }
    /* Il contenuto è già forzato con style inline,
       ma qui possiamo sovrascrivere solo per mobile se serve */
    .banner-content[style] {
        bottom: 0.5rem !important;
        left: 0.5rem !important;
        right: 0.5rem !important;
        max-width: none !important;
        padding: 0.5rem 0.8rem !important;
    }
    .banner-content p[style] {
        font-size: 1rem !important;
    }
    .banner-actions[style] {
        flex-wrap: wrap !important;
        gap: 0.5rem !important;
    }
    .banner-search[style] {
        flex: 1 1 100% !important;
    }
    .banner-search input[style] {
        min-width: 100px !important;
    }
    .banner-button[style] {
        padding: 0.5rem 1rem !important;
        font-size: 0.85rem !important;
    }
}

@media (max-width: 480px) {
    .banner-full {
        margin-top: -1.2rem;
    }
    .banner-content p[style] {
        font-size: 0.85rem !important;
    }
    .banner-search input[style] {
        font-size: 0.85rem !important;
        min-width: 80px !important;
    }
}
</style>
