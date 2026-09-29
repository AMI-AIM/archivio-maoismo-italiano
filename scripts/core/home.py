import html
import os
import re
from collections import Counter

from .site_config import site_path
from .utils import formatta_data, slugify, split_nomi

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
            meta_html_parts.append(f'<span class="doc-type-chip">{html.escape(tipo_display)}</span>')
        if org:
            meta_html_parts.append(f'<span class="doc-org">{html.escape(org)}</span>')
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
    # NOTA: gli stili del dropdown dei suggerimenti (.hero-search-*)
    # vivono in stylesheets/extra.css (sezione 15), non qui.
    banner_html = f"""
<div class="banner-full" style="margin-bottom: 0;">
  <img src="{site_path('immagini/banner.webp')}"
       alt="Archivio del Maoismo Italiano"
       class="banner-image">
  <div class="banner-overlay"></div>
  <div class="banner-content banner-content-home" style="position: absolute; bottom: 0.5rem; left: 0.5rem; z-index: 1; text-align: left; color: #ffffff; max-width: 700px; padding: 0.5rem 1rem;">
    <p style="font-size: 1.4rem; font-weight: 600; opacity: 1; margin: 0 0 0.8rem 0; line-height: 1.45; text-shadow: 0 2px 14px rgba(0,0,0,0.65), 0 1px 3px rgba(0,0,0,0.5);">Documenti, periodici, opuscoli e fonti del movimento "filo-cinese" in Italia</p>
    <div class="banner-actions" style="display: flex; align-items: center; flex-wrap: nowrap; gap: 0.6rem;">
      <a href="documenti/" class="banner-button" style="display: inline-block; padding: 0.5rem 1.2rem; background-color: #ffffff; color: #b71c1c !important; font-weight: 600; font-size: 0.9rem; border-radius: 6px; text-decoration: none; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 2px 12px rgba(0,0,0,0.25); white-space: nowrap; flex-shrink: 0;">Esplora l'archivio</a>
      <form class="banner-search" id="hero-search-form" action="documenti/" method="get" style="display: flex; align-items: center; gap: 0.4rem; background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.4); border-radius: 24px; padding: 0.3rem 0.8rem; backdrop-filter: blur(2px); transition: background 0.2s, border-color 0.2s; position: relative; flex: 1 1 auto; min-width: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="banner-search-icon" aria-hidden="true" style="width: 1.1rem; height: 1.1rem; fill: #ffffff; flex-shrink: 0;">
          <path d="M9.5 3A6.5 6.5 0 0 1 16 9.5c0 1.61-.59 3.09-1.56 4.23l.27.27h.79l5 5-1.5 1.5-5-5v-.79l-.27-.27A6.52 6.52 0 0 1 9.5 16 6.5 6.5 0 0 1 3 9.5 6.5 6.5 0 0 1 9.5 3m0 2C7 5 5 7 5 9.5s2 4.5 4.5 4.5S14 9.5 14 4.5 12 5 9.5 5z"/>
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
title: 'Archivio del Maoismo Italiano - Fonti primarie del movimento filo-cinese in Italia'
description: >-
  Archivio digitale volto alla conservazione e alla valorizzazione di documenti e fonti primarie 
  (volantini, manifesti, periodici, foto...) relative al movimento maoista o 'filo-cinese' in Italia 
  (anni '60-'90). Catalogo ricercabile tramite schede documentarie, biografie di militanti 
  e organizzazioni, percorsi tematici.
hide:
  - toc
---

{banner_html}

<div class="evidenza-band">
  <h2 class="section-title">Documenti in evidenza</h2>
  <div class="evidenza-grid">
"""
        for doc in evidenza_ordinati:
            # FIX: titolo e' dato d'archivio non escapato; viene usato sia
            # come testo visibile sia come attributo (alt/title).
            titolo_html = html.escape(doc['titolo'], quote=True)
            if doc.get('copertina'):
                img_html = f'              <img data-src="{doc["copertina"]}" alt="{titolo_html}" class="lazy-img evidenza-thumbnail-img">'
            else:
                img_html = '              <span class="evidenza-placeholder"></span>'
            home_content += f"""
    <div class="evidenza-card">
        <a href="documenti/{doc['id']}/" class="evidenza-link" title="{titolo_html}">
            <div class="evidenza-thumbnail">
{img_html}
            </div>
            <div class="evidenza-titolo">{titolo_html}</div>
        </a>
    </div>
"""
        home_content += """
  </div>
</div>
"""
    else:
        home_content = f"""---
title: 'Archivio del Maoismo Italiano - Fonti primarie del movimento filo-cinese in Italia'
description: >-
  Archivio digitale volto alla conservazione e alla valorizzazione di documenti e fonti primarie 
  (volantini, manifesti, periodici, foto...) relative al movimento maoista o 'filo-cinese' in Italia 
  (anni '60-'90). Catalogo ricercabile tramite schede documentarie, biografie di militanti 
  e organizzazioni, percorsi tematici.
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
  <h2>
    <svg class="section-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
      <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zM7 12h10v2H7zm0-4h10v2H7zm0 8h6v2H7z"/>
    </svg>
    Aggiunti di recente
  </h2>
  <div class="recent-container">
    <div class="catalogo-lista">
"""
    for s in ultime_tre:
        # FIX: s['data'] e s['titolo'] sono dati d'archivio non escapati;
        # s['meta_html'] e' invece gia' escapato al momento della sua
        # costruzione (vedi sopra), quindi va inserito cosi' com'e'.
        data_html = html.escape(s['data'])
        titolo_html = html.escape(s['titolo'], quote=True)
        home_content += f"""
      <div class="doc-row">
        <div class="doc-data">{data_html}</div>
        <div class="doc-contenuto">
          <div class="doc-titolo"><a href="documenti/{s['id']}/" title="{titolo_html}">{titolo_html}</a></div>
          <div class="doc-meta">{s['meta_html']}</div>
        </div>
      </div>
"""
    home_content += """
    </div>
  </div>
  <div style="text-align: center; margin-top: 1rem;">
    <a href="documenti/" class="md-button md-button--primary">
      <svg class="button-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/>
      </svg>
      Tutti i documenti
    </a>
  </div>
</div>
<div class="home-columns">
"""

    # ============================================================
    # COLONNA 1: Persone più menzionate
    # ============================================================
    home_content += """
<div class="home-column">
  <h2>
    <svg class="section-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
    </svg>
    Persone più menzionate
  </h2>
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
            # FIX: nome, date_vita e le iniziali derivate da nome sono
            # dati d'archivio non escapati.
            nome_html = html.escape(nome)
            date_vita_html = html.escape(date_vita)
            iniziali_html = html.escape(estrai_iniziali(nome))
            home_content += f"""
      <div class="doc-row doc-row-persona">
        <div class="persona-avatar persona-avatar--{rank}">
          <span class="persona-iniziali">{iniziali_html}</span>
          <span class="persona-rank-badge persona-rank-badge--{rank}">{rank}</span>
        </div>
        <div class="doc-contenuto">
          <div class="doc-titolo"><a href="persone/{slug}/">{nome_html}</a></div>
          <div class="doc-sommario">{etichetta_conteggio}</div>
          {f'<div class="persona-date">{date_vita_html}</div>' if date_vita_html else ''}
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
    <a href="persone/" class="md-button md-button--primary">
      <svg class="button-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 2c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
      </svg>
      Tutte le persone
    </a>
  </div>
</div>
"""

    # ============================================================
    # COLONNA 2: Organizzazioni più menzionate
    # Icona: SVG inline "flag" (bandiera) — nessuna dipendenza esterna
    # ============================================================
    home_content += """
<div class="home-column">
  <h2>
    <svg class="section-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
      <path d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z"/>
    </svg>
    Organizzazioni più menzionate
  </h2>
  <div class="recent-container">
    <div class="catalogo-lista">
"""
    if organizzazioni_top:
        for rank, (nome, conteggio) in enumerate(organizzazioni_top, start=1):
            info_org = (organizzazioni or {}).get(nome, {})
            slug = info_org.get('slug', slugify(nome))
            etichetta_conteggio = "1 documento collegato" if conteggio == 1 else f"{conteggio} documenti collegati"
            nome_html = html.escape(nome)
            iniziali_html = html.escape(estrai_iniziali(nome))
            home_content += f"""
      <div class="doc-row doc-row-persona">
        <div class="persona-avatar persona-avatar--{rank}">
          <span class="persona-iniziali">{iniziali_html}</span>
          <span class="persona-rank-badge persona-rank-badge--{rank}">{rank}</span>
        </div>
        <div class="doc-contenuto">
          <div class="doc-titolo"><a href="organizzazioni/{slug}/">{nome_html}</a></div>
          <div class="doc-sommario">{etichetta_conteggio}</div>
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
    <a href="organizzazioni/" class="md-button md-button--primary">
      <svg class="button-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z"/>
      </svg>
      Tutte le organizzazioni
    </a>
  </div>
</div>
</div>
"""

    # Gli stili della home (circa 550 righe storiche) sono migrati in
    # assets/stylesheets/home.css: niente piu CSS inline nel markdown.
    # Il <link> va in coda al contenuto, DOPO le sezioni che usano le
    # classi banner-*: il file e' caricato dopo extra.css (che arriva
    # nell'<head> del tema), quindi mantiene la stessa cascata che il
    # blocco inline aveva prima della migrazione -- in particolare per
    # body:has(.banner-content-home) .lazy-skeleton (skeleton grigio
    # scuro della home, definito in extra.css).
    home_content += f"""
<link rel="stylesheet" href="{site_path('stylesheets/home.css')}">
"""


    index_path = os.path.join(output_dir, 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(home_content)
    print(f"Home generata con {len(ultime_tre)} ultimi documenti.")