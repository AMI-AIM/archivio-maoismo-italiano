import os
import re
from collections import Counter
from .utils import formatta_data, split_nomi, slugify
from .site_config import site_path


# DOCUMENTI IN EVIDENZA: inserisci qui gli ID dei documenti che vuoi mostrare
EVIDENZA_IDS = [
    'AMI-0049',
    'AMI-0045',
    'AMI-0043',
    'AMI-0013',
    'AMI-0035'
]


def estrai_iniziali(nome, max_lettere=2):
    """Estrae le iniziali dalle prime due parole significative
    (scarta quelle che iniziano con punteggiatura, es. parentesi).
    Es. 'Mao Zedong' -> 'MZ';
        'Partito Comunista d'Italia (marxista-leninista)' -> 'PC'."""
    parti = [p for p in nome.split() if p and p[0].isalnum()]
    if not parti:
        return '?'
    if len(parti) == 1:
        return parti[0][:max_lettere].upper()
    return ''.join(p[0] for p in parti[:max_lettere]).upper()


def genera_home(df, persone, output_dir, organizzazioni=None):
    print("\nGenerazione della Home page...")

    schede = []
    conteggio_persone = Counter()
    conteggio_organizzazioni = Counter()
    documenti_evidenza = []

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

        tipo_raw = str(row.get('tipo', '')).strip()
        if tipo_raw in ['nan', 'None']:
            tipo_raw = ''
        tipo = tipo_raw.lower()
        tipo_display = 'testo' if tipo == 'testo_bilingue' else tipo
        tipo_display = tipo_display.capitalize() if tipo_display else ''

        org = str(row.get('organizzazione', '')).strip()
        if org in ['nan', 'None']:
            org = ''

        url_ia = str(row.get('url', '#')).strip()
        identifier = None
        if url_ia and url_ia != '#':
            match = re.search(r'/details/([^/?#]+)', url_ia)
            if match:
                identifier = match.group(1)

        if identifier:
            copertina_url = f"https://archive.org/services/img/{identifier}"
        else:
            copertina_url = None

        parti_sommario = []
        if tipo:
            parti_sommario.append(tipo)
        if org:
            parti_sommario.append(org)
        sommario = ' \u00b7 '.join(parti_sommario) if parti_sommario else 'Documento storico'

        meta_html_parts = []
        if tipo_display:
            meta_html_parts.append(f'<span class="doc-type-chip">{tipo_display}</span>')
        if org:
            meta_html_parts.append(f'<span class="doc-org">{org}</span>')
        meta_html = ''.join(meta_html_parts) if meta_html_parts else '<span class="doc-org">Documento storico</span>'

        try:
            num_id = int(re.search(r'(\d+)', ami_id).group(1))
        except Exception:
            num_id = 0

        schede.append({
            'id': ami_id,
            'titolo': titolo,
            'data': data_formattata,
            'sommario': sommario,
            'meta_html': meta_html,
            'num_id': num_id
        })

        if ami_id in EVIDENZA_IDS:
            documenti_evidenza.append({
                'id': ami_id,
                'titolo': titolo,
                'data': data_formattata,
                'sommario': sommario,
                'meta_html': meta_html,
                'num_id': num_id,
                'copertina': copertina_url
            })

        # ---- Conteggio PERSONE (autore + persone_collegate) ----
        autore_raw = str(row.get('autore', '')).strip()
        persone_collegate_raw = str(row.get('persone_collegate', '')).strip()
        nomi_da_contare = set()
        if autore_raw and autore_raw not in ['nan', 'None']:
            nomi_da_contare.update(split_nomi(autore_raw))
        if persone_collegate_raw and persone_collegate_raw not in ['nan', 'None']:
            nomi_da_contare.update(split_nomi(persone_collegate_raw))
        for nome in nomi_da_contare:
            if nome in persone:
                conteggio_persone[nome] += 1

        # ---- Conteggio ORGANIZZAZIONI (organizzazione + organizzazioni_collegate) ----
        org_raw = str(row.get('organizzazione', '')).strip()
        org_collegate_raw = str(row.get('organizzazioni_collegate', '')).strip()
        org_da_contare = set()
        if org_raw and org_raw not in ['nan', 'None']:
            org_da_contare.update(split_nomi(org_raw))
        if org_collegate_raw and org_collegate_raw not in ['nan', 'None']:
            org_da_contare.update(split_nomi(org_collegate_raw))
        for nome in org_da_contare:
            if organizzazioni is None or nome in organizzazioni:
                conteggio_organizzazioni[nome] += 1

    schede.sort(key=lambda x: x['num_id'], reverse=True)
    ultime_tre = schede[:3]

    evidenza_ordinati = []
    for id_target in EVIDENZA_IDS:
        for doc in documenti_evidenza:
            if doc['id'] == id_target:
                evidenza_ordinati.append(doc)
                break

    persone_top = conteggio_persone.most_common(3)
    organizzazioni_top = conteggio_organizzazioni.most_common(3)

    # BANNER — testo più grande e spesso per leggibilità
    banner_html = f"""
<div class="banner-full" style="margin-bottom: 0;">
    <img src="{site_path('immagini/banner.webp')}"
         alt="Archivio del Maoismo Italiano"
         class="banner-image">
    <div class="banner-overlay"></div>
    <div class="banner-content" style="position: absolute; bottom: 0.5rem; left: 0.5rem; z-index: 1; text-align: left; color: #ffffff; max-width: 700px; padding: 0.5rem 1rem;">
        <p style="font-size: 1.4rem; font-weight: 600; opacity: 1; margin: 0 0 0.8rem 0; line-height: 1.45; text-shadow: 0 2px 14px rgba(0,0,0,0.65), 0 1px 3px rgba(0,0,0,0.5);">Documenti, periodici, opuscoli e fonti del movimento "filo-cinese" in Italia</p>
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

    # SEZIONE DOCUMENTI IN EVIDENZA (con tooltip sui titoli)
    if evidenza_ordinati:
        home_content = f"""---
title: "Archivio del Maoismo Italiano — documenti, periodici e fonti del movimento filo-cinese"
description: "Archivio digitale di documenti, periodici, opuscoli e fonti primarie del movimento politico 'filo-cinese' in Italia (anni '60-'80). Catalogo ricercabile con schede catalografiche, biografie e organizzazioni."
hide:
  - toc
---
{banner_html}
<div class="evidenza-band">
    <h2 class="section-title">Documenti in evidenza</h2>
    <div class="evidenza-grid">
"""
        for doc in evidenza_ordinati:
            if doc.get('copertina'):
                img_html = f'            <img src="{doc["copertina"]}" alt="{doc["titolo"]}" class="evidenza-thumbnail-img" loading="lazy">'
            else:
                img_html = '            <span class="evidenza-placeholder"></span>'

            home_content += f"""
        <div class="evidenza-card">
            <a href="documenti/{doc['id']}/" class="evidenza-link" title="{doc['titolo']}">
                <div class="evidenza-thumbnail">
{img_html}
                </div>
                <div class="evidenza-titolo">{doc['titolo']}</div>
            </a>
        </div>
"""
        home_content += """
    </div>
</div>
"""
    else:
        home_content = f"""---
title: "Archivio del Maoismo Italiano — documenti, periodici e fonti del movimento filo-cinese"
description: "Archivio digitale di documenti, periodici, opuscoli e fonti primarie del movimento politico 'filo-cinese' in Italia (anni '60-'80). Catalogo ricercabile con schede catalografiche, biografie e organizzazioni."
hide:
  - toc
---
{banner_html}
"""

    # ============================================================
    # AGGIUNTI DI RECENTE — sezione piena larghezza, SOPRA le colonne
    # ============================================================
    home_content += """
<div class="home-column home-recent">
    <h2><svg class="section-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zM7 12h10v2H7zm0-4h10v2H7zm0 8h6v2H7z"/></svg> Aggiunti di recente</h2>
    <div class="recent-container">
        <div class="catalogo-lista">
"""
    for s in ultime_tre:
        home_content += f"""
            <div class="doc-row">
                <div class="doc-data">{s['data']}</div>
                <div class="doc-contenuto">
                    <div class="doc-titolo"><a href="documenti/{s['id']}/" title="{s['titolo']}">{s['titolo']}</a></div>
                    <div class="doc-meta">{s['meta_html']}</div>
                </div>
            </div>
"""
    home_content += """
        </div>
    </div>
    <div style="text-align: center; margin-top: 1rem;">
        <a href="documenti/" class="md-button md-button--primary"><svg class="button-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg> Tutti i documenti</a>
    </div>
</div>

<div class="home-columns">
"""

    # ============================================================
    # COLONNA 1: Persone più menzionate
    # ============================================================
    home_content += """
<div class="home-column">
    <h2><svg class="section-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg> Persone più menzionate</h2>
    <div class="recent-container">
        <div class="catalogo-lista">
"""
    if persone_top:
        for rank, (nome, conteggio) in enumerate(persone_top, start=1):
            info_persona = persone.get(nome, {})
            slug = info_persona.get('slug', slugify(nome))
            nascita = str(info_persona.get('nascita', '')).strip()
            morte = str(info_persona.get('morte', '')).strip()
            date_vita = ' \u2013 '.join([d for d in [nascita, morte] if d and d not in ['nan', 'None', '']])
            etichetta_conteggio = "1 documento collegato" if conteggio == 1 else f"{conteggio} documenti collegati"
            iniziali = estrai_iniziali(nome)

            home_content += f"""
            <div class="doc-row doc-row-persona">
                <div class="persona-avatar persona-avatar--{rank}">
                    <span class="persona-iniziali">{iniziali}</span>
                    <span class="persona-rank-badge persona-rank-badge--{rank}">{rank}</span>
                </div>
                <div class="doc-contenuto">
                    <div class="doc-titolo"><a href="persone/{slug}/">{nome}</a></div>
                    <div class="doc-sommario">{etichetta_conteggio}</div>
                    {f'<div class="persona-date">{date_vita}</div>' if date_vita else ''}
                </div>
            </div>
"""
    else:
        home_content += """
            <p style="padding: 0.6rem 0.8rem; color: var(--md-default-fg-color--light);">Nessuna persona ancora collegata ai documenti.</p>
"""
    home_content += """
        </div>
    </div>
    <div style="text-align: center; margin-top: 1rem;">
        <a href="persone/" class="md-button md-button--primary"><svg class="button-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg> Tutte le persone</a>
    </div>
</div>
"""

    # ============================================================
    # COLONNA 2: Organizzazioni più menzionate
    # Icona: SVG inline "flag" (bandiera) — nessuna dipendenza esterna
    # ============================================================
    home_content += """
<div class="home-column">
    <h2><svg class="section-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z"/></svg> Organizzazioni più menzionate</h2>
    <div class="recent-container">
        <div class="catalogo-lista">
"""
    if organizzazioni_top:
        for rank, (nome, conteggio) in enumerate(organizzazioni_top, start=1):
            info_org = (organizzazioni or {}).get(nome, {})
            slug = info_org.get('slug', slugify(nome))
            data_range = str(info_org.get('data_range', '')).strip()
            if data_range in ['nan', 'None']:
                data_range = ''
            etichetta_conteggio = "1 documento collegato" if conteggio == 1 else f"{conteggio} documenti collegati"
            iniziali = estrai_iniziali(nome)

            home_content += f"""
            <div class="doc-row doc-row-persona">
                <div class="persona-avatar persona-avatar--{rank}">
                    <span class="persona-iniziali">{iniziali}</span>
                    <span class="persona-rank-badge persona-rank-badge--{rank}">{rank}</span>
                </div>
                <div class="doc-contenuto">
                    <div class="doc-titolo"><a href="organizzazioni/{slug}/">{nome}</a></div>
                    <div class="doc-sommario">{etichetta_conteggio}</div>
                    {f'<div class="persona-date">{data_range}</div>' if data_range else ''}
                </div>
            </div>
"""
    else:
        home_content += """
            <p style="padding: 0.6rem 0.8rem; color: var(--md-default-fg-color--light);">Nessuna organizzazione ancora collegata ai documenti.</p>
"""
    home_content += """
        </div>
    </div>
    <div style="text-align: center; margin-top: 1rem;">
        <a href="organizzazioni/" class="md-button md-button--primary"><svg class="button-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z"/></svg> Tutte le organizzazioni</a>
    </div>
</div>
</div>
"""

    # STILI
    home_content += """
<style>
/* Nasconde il titolo "Home" nella pagina */
.md-content article h1:first-of-type {
    display: none !important;
}

/* ------------------------------------------------------------
BANNER
------------------------------------------------------------ */
.banner-full {
    position: relative;
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    margin-bottom: 0 !important;
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

/* Placeholder ricerca più leggibile */
#hero-search-input::placeholder {
    color: #e0e0e0 !important;
    opacity: 1 !important;
}

/* ------------------------------------------------------------
SEZIONE DOCUMENTI IN EVIDENZA
------------------------------------------------------------ */
.evidenza-band {
    position: relative;
    padding: 1.5rem 0 1.2rem;
    margin: 0 0 2rem 0;
}
.evidenza-band::before {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    left: calc(-50vw + 50%);
    right: calc(-50vw + 50%);
    background: #0d0d0d;
    z-index: -1;
}
.evidenza-band .section-title {
    margin: 0 0 1.5rem 0;
}
.section-title {
    font-size: 1.5rem;
    font-weight: 600;
    display: block;
    color: #ffffff;
    padding-bottom: 0.5rem;
    position: relative;
}
.section-title::after {
    content: "";
    display: block;
    width: 60px;
    height: 3px;
    background: #b71c1c;
    margin-top: 0.4rem;
    border-radius: 2px;
}
.section-icon {
    width: 1.4rem;
    height: 1.4rem;
    fill: var(--md-primary-fg-color);
    flex-shrink: 0;
}

/* Riga flex: larghezza card = larghezza copertina, spazi uniformi */
.evidenza-grid {
    display: flex !important;
    flex-wrap: nowrap !important;
    justify-content: space-between !important;
    align-items: flex-start !important;
    gap: 1.5rem !important;
    overflow-x: auto;
    padding-bottom: 2.6rem;
    margin-bottom: 0;
    scrollbar-width: none;
    -ms-overflow-style: none;
}
.evidenza-grid::-webkit-scrollbar {
    display: none;
}
.evidenza-card {
    position: relative;
    flex: 0 0 auto !important;
    min-width: 0;
    transition: transform 0.25s ease;
}
.evidenza-card:hover {
    transform: translateY(-4px);
}
.evidenza-link {
    display: block;
    text-decoration: none;
    color: inherit;
}
.evidenza-thumbnail {
    height: 240px !important;
    max-height: 240px !important;
    display: flex;
    align-items: center;
    justify-content: center;
}
.evidenza-thumbnail-img {
    display: block !important;
    height: 100% !important;
    max-height: 240px !important;
    width: auto !important;
    max-width: 100% !important;
    object-fit: contain !important;
}
.evidenza-placeholder {
    color: #ffffff;
    font-size: 2.5rem;
    opacity: 0.5;
}
.evidenza-titolo {
    position: absolute !important;
    top: 100% !important;
    left: 0 !important;
    right: 0 !important;
    margin-top: 0.75rem !important;
    font-size: 0.85rem;
    font-weight: 500;
    line-height: 1.3;
    color: rgba(255, 255, 255, 0.92);
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ------------------------------------------------------------
CATALOGO
------------------------------------------------------------ */
.catalogo-lista {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}
.doc-row {
    display: flex;
    align-items: flex-start;
    padding: 0.75rem 0.9rem;
    border-bottom: 1px solid var(--md-default-fg-color--lightest);
    border-left: 3px solid transparent;
    transition: background-color 0.15s, border-left-color 0.15s;
    gap: 1.5rem;
}
.doc-row:last-child {
    border-bottom: none;
}
.doc-row:hover {
    background-color: var(--md-code-bg-color);
    border-left-color: var(--md-primary-fg-color);
}
.doc-row-persona {
    gap: 1rem;
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
.doc-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.15rem;
}
.doc-type-chip {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--md-primary-fg-color);
    background: rgba(183, 28, 28, 0.1);
    padding: 0.15rem 0.55rem;
    border-radius: 20px;
    white-space: nowrap;
}
.doc-org {
    font-size: 0.88rem;
    color: var(--md-default-fg-color--light);
}
.doc-sommario {
    font-size: 0.9rem;
    color: var(--md-default-fg-color--light);
}
.recent-container {
    background: var(--md-code-bg-color);
    border-radius: 14px;
    padding: 0.5rem 0.5rem 0.2rem 0.5rem;
    margin: 1rem 0;
    border: 1px solid var(--md-default-fg-color--lightest);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

/* ------------------------------------------------------------
LAYOUT HOME: recenti a piena larghezza SOPRA, poi due colonne 1:1
------------------------------------------------------------ */
.home-recent {
    margin: 0.5rem 0 2rem 0;
}
.home-columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    align-items: stretch;
    margin-top: 0.5rem;
}
.home-column {
    display: flex;
    flex-direction: column;
}
.home-column h2 {
    margin-top: 0;
    margin-bottom: 0.6rem;
    font-size: 1.3rem;
    display: block;
    padding-bottom: 0.5rem;
    position: relative;
}
.home-column h2::after {
    content: "";
    display: block;
    width: 60px;
    height: 3px;
    background: #b71c1c;
    margin-top: 0.4rem;
    border-radius: 2px;
}
.button-icon {
    width: 1rem;
    height: 1rem;
    fill: currentColor;
    vertical-align: -0.15em;
    margin-right: 0.3rem;
}
.home-column .recent-container {
    flex: 1;
    display: flex;
    flex-direction: column;
}
.home-column .catalogo-lista {
    flex: 1;
}

/* ------------------------------------------------------------
AVATAR con iniziali + badge rank (persone E organizzazioni)
------------------------------------------------------------ */
.persona-avatar {
    position: relative;
    flex: 0 0 52px;
    width: 52px;
    height: 52px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
    flex-shrink: 0;
}
.persona-avatar--1 { background: #b71c1c; }
.persona-avatar--2 { background: #424242; }
.persona-avatar--3 { background: #8d6e63; }
.persona-iniziali {
    font-weight: 700;
    font-size: 1.05rem;
    color: #ffffff;
    letter-spacing: 0.05em;
    user-select: none;
}
.persona-rank-badge {
    position: absolute;
    top: -4px;
    right: -4px;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 700;
    color: #1a1a1a;
    border: 2px solid var(--md-code-bg-color);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}
.persona-rank-badge--1 { background: linear-gradient(135deg, #f6d365, #c9911d); }
.persona-rank-badge--2 { background: linear-gradient(135deg, #dde3e6, #9aa5ab); }
.persona-rank-badge--3 { background: linear-gradient(135deg, #d7a06e, #a05a2c); }
.persona-date {
    font-size: 0.8rem;
    color: var(--md-default-fg-color--light);
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

/* ------------------------------------------------------------
DROPDOWN SUGGERIMENTI RICERCA HERO
------------------------------------------------------------ */
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
    line-height: 1.5;
}
.hero-search-item-tag {
    display: inline-block;
    vertical-align: middle;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    padding: 0.1rem 0.45rem;
    border-radius: 10px;
    color: #ffffff;
    white-space: nowrap;
    margin-left: 0.4em;
}
.hero-search-item-tag--persona { background: #6a1b9a; }
.hero-search-item-tag--organizzazione { background: #1565c0; }
.hero-search-item-tag--documento { background: #b71c1c; }
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

/* ------------------------------------------------------------
RESPONSIVE
------------------------------------------------------------ */
@media (max-width: 1100px) {
    .evidenza-thumbnail {
        height: 190px !important;
        max-height: 190px !important;
    }
    .evidenza-thumbnail-img {
        max-height: 190px !important;
    }
}

@media (max-width: 768px) {
    /* Le due colonne diventano impilate */
    .home-columns {
        grid-template-columns: 1fr;
        gap: 0.5rem;
    }

    .evidenza-grid {
        justify-content: flex-start !important;
        scroll-snap-type: x mandatory;
        -webkit-overflow-scrolling: touch;
        padding: 0 1rem 2.4rem 1rem !important;
        margin: 0 -1rem !important;
        gap: 1.25rem !important;
    }
    .evidenza-card {
        scroll-snap-align: start;
    }
    .evidenza-band {
        padding: 0.9rem 0 1rem;
    }
    .evidenza-band .section-title {
        margin: 0 0 1.2rem 0;
        font-size: 1.25rem;
    }
    .evidenza-thumbnail {
        height: 200px !important;
        max-height: 200px !important;
    }
    .evidenza-titolo {
        font-size: 0.8rem;
    }

    .banner-full {
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
        font-size: 0.85rem !important;
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

@media (max-width: 600px) {
    .evidenza-thumbnail {
        height: 170px !important;
        max-height: 170px !important;
    }
    .evidenza-thumbnail-img {
        max-height: 170px !important;
    }
    .doc-row {
        flex-direction: column;
        gap: 0.1rem;
        padding: 0.6rem 0.2rem;
    }
    .doc-row-persona {
        flex-direction: row;
        gap: 1rem;
    }
    .doc-data {
        flex: 0 0 auto;
        white-space: normal;
        font-size: 0.8rem;
    }
    .doc-titolo {
        font-size: 0.95rem;
    }
    .doc-sommario {
        font-size: 0.8rem;
    }
}

@media (max-width: 480px) {
    .section-title {
        font-size: 1.2rem;
    }
    .evidenza-thumbnail {
        height: 150px !important;
        max-height: 150px !important;
    }
    .evidenza-thumbnail-img {
        max-height: 150px !important;
    }
    .banner-full {
        height: 180px;
        min-height: 150px;
    }
    .banner-content p[style] {
        font-size: 0.75rem !important;
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
