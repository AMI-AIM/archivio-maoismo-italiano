import os
import re
import html
import json
import pandas as pd
from .utils import formatta_data, split_nomi, scarica_descrizione_ia, scarica_testo_ia
from .soggetti import crea_link, link_lista

def crea_schede(df, persone, organizzazioni, output_dir):
    print("📄 Creazione delle schede dei documenti...")
    
    documenti_dir = os.path.join(output_dir, 'documenti')
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
        
        luogo_raw = str(row.get('luogo', '')).strip()
        if luogo_raw in ['nan', 'None']:
            luogo_raw = ''
        
        editore_raw = str(row.get('editore', '')).strip()
        if editore_raw in ['nan', 'None']:
            editore_raw = ''
        
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
        
        tipo_raw = str(row.get('tipo', '')).strip()
        if tipo_raw in ['nan', 'None']:
            tipo_raw = ''
        tipo = tipo_raw.lower()
        if tipo == 'fotografia':
            tipo = 'foto'
        
        # 🔥 PER IL DISPLAY: "testo_bilingue" viene mostrato come "testo" con maiuscola
        tipo_display = 'testo' if tipo == 'testo_bilingue' else tipo
        tipo_display = tipo_display.capitalize() if tipo_display else ''
        
        serie = str(row.get('serie', '')).strip()
        if serie in ['nan', 'None']:
            serie = ''
        
        # 🔥 KEYWORDS RIMOSSE
        
        url_ia = str(row.get('url', '#')).strip()
        if url_ia in ['nan', 'None', '']:
            url_ia = '#'
        
        nome_file = str(row.get('nome_file', '')).strip()
        if nome_file in ['nan', 'None']:
            nome_file = ''
        
        nome_file_originale = str(row.get('nome_file_originale', '')).strip()
        if nome_file_originale in ['nan', 'None']:
            nome_file_originale = ''
        nome_file_traduzione = str(row.get('nome_file_traduzione', '')).strip()
        if nome_file_traduzione in ['nan', 'None']:
            nome_file_traduzione = ''
        
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
        
        # ============================================================
        # 🔥 CITAZIONE
        # ============================================================
        anno_citazione = data_formattata if data_formattata else 's.d.'
        permalink = f"https://ami-aim.github.io/archivio-maoismo-italiano/documenti/{ami_id}/"
        citazione_id = ami_id.lower().replace('-', '_')
        
        is_bibliografico = tipo in ['libro', 'opuscolo']
        
        citazione_bottone_html = (
            f'<button class="citazione-link" type="button" '
            f'id="citazione-toggle-{citazione_id}">📑 Cita questo documento</button>'
        )
        
        if is_bibliografico:
            def formatta_autore_bibliografico(nome_completo):
                info = persone.get(nome_completo)
                if info and info.get('cognome'):
                    cognome = info['cognome'].strip()
                    resto = nome_completo.replace(cognome, '', 1).strip(' ,')
                    return f'{cognome}, {resto}' if resto else cognome
                return nome_completo
            
            if autore_raw:
                autori_lista = split_nomi(autore_raw)
                autore_citazione = '; '.join(formatta_autore_bibliografico(a) for a in autori_lista)
            elif editore_raw:
                autore_citazione = editore_raw
            elif org_raw:
                autore_citazione = org_raw
            else:
                autore_citazione = 'Archivio del Maoismo Italiano (a cura di)'
            
            editore_citazione = editore_raw if editore_raw else org_raw
            
            luogo_editore = ''
            if luogo_raw and editore_citazione:
                luogo_editore = f'{luogo_raw}: {editore_citazione}, '
            elif editore_citazione:
                luogo_editore = f'{editore_citazione}, '
            elif luogo_raw:
                luogo_editore = f'{luogo_raw}, '
            
            citazione_chicago = (
                f'{autore_citazione}. "{titolo}". '
                f'{luogo_editore}{anno_citazione}. Archivio del Maoismo Italiano ({ami_id}). '
                f'{permalink}.'
            )
            
            citazione_mla = (
                f'{autore_citazione}. "{titolo}". '
                + (f'{editore_citazione}, ' if editore_citazione else '')
                + f'{anno_citazione}. Archivio del Maoismo Italiano ({ami_id}), {permalink}.'
            )
            
            bibtex_key = citazione_id
            bibtex_type = 'book' if tipo == 'libro' else 'booklet'
            citazione_bibtex = (
                '@' + bibtex_type + '{' + bibtex_key + ',\n'
                '  title = {' + titolo + '},\n'
                '  author = {' + autore_citazione + '},\n'
                '  year = {' + anno_citazione + '},\n'
                + (('  publisher = {' + editore_citazione + '},\n') if editore_citazione else '')
                + (('  address = {' + luogo_raw + '},\n') if luogo_raw else '')
                + '  note = {Archivio del Maoismo Italiano, ' + ami_id + '. ' + permalink + '}\n'
                '}'
            )
            
            citazione_semplice = (
                f'{autore_citazione}, {titolo}'
                + (f', {luogo_raw}: {editore_citazione}' if luogo_raw and editore_citazione else (f', {editore_citazione}' if editore_citazione else ''))
                + f', {anno_citazione}. Archivio del Maoismo Italiano ({ami_id}). {permalink}'
            )
            
            citazioni_dict = {
                'chicago': citazione_chicago,
                'mla': citazione_mla,
                'bibtex': citazione_bibtex,
                'semplice': citazione_semplice
            }
            citazioni_json = json.dumps(citazioni_dict, ensure_ascii=False)
        else:
            citazione_minima = f'"{titolo}", {anno_citazione}. Archivio del Maoismo Italiano. {permalink}'
            citazione_minima_html = html.escape(citazione_minima)
        
        # 🔥 FRONTMATTER SENZA KEYWORDS
        frontmatter = f"""---
title: "{titolo}"
ami_id: {ami_id}
organization: "{org_raw}"
author: "{autore_raw}"
year: "{data_formattata}"
type: "{tipo}"
series: "{serie}"
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

        # 🔥 GESTIONE FOTO
        if tipo == 'foto' and identifier:
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
            {citazione_bottone_html}
            <a href="{url_ia}" target="_blank">🔗 Apri su Internet Archive</a>
        </div>
    </div>
"""
        
        # 🔥 GESTIONE TESTO BILINGUE
        elif tipo == 'testo_bilingue' and identifier:
            testo_originale = scarica_testo_ia(identifier, nome_file_originale) if nome_file_originale else None
            testo_traduzione = scarica_testo_ia(identifier, nome_file_traduzione) if nome_file_traduzione else None
            
            if testo_originale:
                testo_originale = html.escape(testo_originale)
            else:
                testo_originale = 'Testo originale non disponibile.'
            
            if testo_traduzione:
                testo_traduzione = html.escape(testo_traduzione)
            else:
                testo_traduzione = 'Traduzione non disponibile.'
            
            content += f"""
    <div class="text-bilingue">
        <div class="lingua-toggle" data-toggle-container>
            <button class="lingua-btn lingua-btn--active" data-lingua="originale">Originale</button>
            <button class="lingua-btn" data-lingua="traduzione">Traduzione</button>
        </div>
        <div class="lingua-content lingua-content--originale" data-lingua-content="originale">
            <pre class="text-preview">{testo_originale}</pre>
        </div>
        <div class="lingua-content lingua-content--traduzione" data-lingua-content="traduzione" style="display:none;">
            <pre class="text-preview">{testo_traduzione}</pre>
        </div>
    </div>
    <div class="embed-footer">
        {citazione_bottone_html}
        <a href="{url_ia}" target="_blank">🔗 Apri su Internet Archive</a>
    </div>
"""
            content += """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const container = document.querySelector('[data-toggle-container]');
        if (!container) return;
        const buttons = container.querySelectorAll('.lingua-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', function() {
                const lingua = this.dataset.lingua;
                buttons.forEach(b => b.classList.remove('lingua-btn--active'));
                this.classList.add('lingua-btn--active');
                document.querySelectorAll('[data-lingua-content]').forEach(el => {
                    el.style.display = el.dataset.linguaContent === lingua ? '' : 'none';
                });
            });
        });
    });
    </script>
"""
        
        # 🔥 GESTIONE TESTO/TRASCRIZIONE
        elif tipo in ['testo', 'trascrizione'] and identifier:
            testo = scarica_testo_ia(identifier, nome_file)
            if testo:
                testo = html.escape(testo)
                content += f"""
    <div class="text-content">
        <pre class="text-preview">{testo}</pre>
    </div>
"""
            else:
                content += f"""
    <div class="text-fallback">
        <p>🔗 <a href="{url_ia}" target="_blank">Visualizza il testo su Internet Archive</a></p>
    </div>
"""
            content += f"""
    <div class="embed-footer">
        {citazione_bottone_html}
        <a href="{url_ia}" target="_blank">🔗 Apri su Internet Archive</a>
    </div>
"""
        
        # 🔥 GESTIONE AUDIO, PDF, ETC.
        elif identifier:
            if tipo == 'audio':
                embed_url = f"https://archive.org/embed/{identifier}"
            else:
                embed_url = f"https://archive.org/embed/{identifier}?ui=embed&nav=0"
            
            content += f"""
    <iframe src="{embed_url}" 
            class="universal-embed" 
            allowfullscreen>
    </iframe>
    <div class="embed-footer">
        {citazione_bottone_html}
        <a href="{url_ia}" target="_blank">🔗 Apri su Internet Archive</a>
    </div>
"""
        else:
            content += f"""
    <div class="no-embed">
        <p>📄 <a href="{url_ia}" target="_blank">Visualizza il documento su Internet Archive</a></p>
    </div>
    <div class="embed-footer">
        {citazione_bottone_html}
    </div>
"""

        # Pannello citazione
        if is_bibliografico:
            content += f"""
<div class="citazione-pannello" id="citazione-pannello-{citazione_id}" style="display:none;">
    <div class="citazione-tabs">
        <button class="citazione-tab citazione-tab--active" data-formato="chicago" type="button">Chicago</button>
        <button class="citazione-tab" data-formato="mla" type="button">MLA</button>
        <button class="citazione-tab" data-formato="bibtex" type="button">BibTeX</button>
        <button class="citazione-tab" data-formato="semplice" type="button">Semplice</button>
    </div>
    <textarea class="citazione-testo" id="citazione-testo-{citazione_id}" readonly rows="4"></textarea>
    <button class="citazione-copia" id="citazione-copia-{citazione_id}" type="button">📋 Copia</button>
</div>
</div>

<script type="application/json" id="citazioni-dati-{citazione_id}">{citazioni_json}</script>
<script>
(function() {{
    const datiEl = document.getElementById('citazioni-dati-{citazione_id}');
    const toggleBtn = document.getElementById('citazione-toggle-{citazione_id}');
    const pannello = document.getElementById('citazione-pannello-{citazione_id}');
    const textarea = document.getElementById('citazione-testo-{citazione_id}');
    const copiaBtn = document.getElementById('citazione-copia-{citazione_id}');
    if (!datiEl || !toggleBtn || !pannello) return;
    const citazioni = JSON.parse(datiEl.textContent);
    const tabs = pannello.querySelectorAll('.citazione-tab');

    function mostraFormato(formato) {{
        textarea.value = citazioni[formato] || '';
        tabs.forEach(function(t) {{
            t.classList.toggle('citazione-tab--active', t.dataset.formato === formato);
        }});
    }}
    mostraFormato('chicago');

    toggleBtn.addEventListener('click', function() {{
        const aperto = pannello.style.display !== 'none';
        pannello.style.display = aperto ? 'none' : 'block';
    }});

    tabs.forEach(function(tab) {{
        tab.addEventListener('click', function() {{ mostraFormato(tab.dataset.formato); }});
    }});

    if (copiaBtn && textarea) {{
        copiaBtn.addEventListener('click', function() {{
            textarea.select();
            const testoOriginaleBtn = copiaBtn.textContent;
            function confermaCopia() {{
                copiaBtn.textContent = '✅ Copiato!';
                setTimeout(function() {{ copiaBtn.textContent = testoOriginaleBtn; }}, 1500);
            }}
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(textarea.value).then(confermaCopia).catch(function() {{
                    document.execCommand('copy');
                    confermaCopia();
                }});
            }} else {{
                document.execCommand('copy');
                confermaCopia();
            }}
        }});
    }}
}})();
</script>
"""
        else:
            content += f"""
<div class="citazione-pannello" id="citazione-pannello-{citazione_id}" style="display:none;">
    <textarea class="citazione-testo" id="citazione-testo-{citazione_id}" readonly rows="3">{citazione_minima_html}</textarea>
    <button class="citazione-copia" id="citazione-copia-{citazione_id}" type="button">📋 Copia</button>
</div>
</div>

<script>
(function() {{
    const toggleBtn = document.getElementById('citazione-toggle-{citazione_id}');
    const pannello = document.getElementById('citazione-pannello-{citazione_id}');
    const textarea = document.getElementById('citazione-testo-{citazione_id}');
    const copiaBtn = document.getElementById('citazione-copia-{citazione_id}');
    if (!toggleBtn || !pannello) return;

    toggleBtn.addEventListener('click', function() {{
        const aperto = pannello.style.display !== 'none';
        pannello.style.display = aperto ? 'none' : 'block';
    }});

    if (copiaBtn && textarea) {{
        copiaBtn.addEventListener('click', function() {{
            textarea.select();
            const testoOriginaleBtn = copiaBtn.textContent;
            function confermaCopia() {{
                copiaBtn.textContent = '✅ Copiato!';
                setTimeout(function() {{ copiaBtn.textContent = testoOriginaleBtn; }}, 1500);
            }}
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(textarea.value).then(confermaCopia).catch(function() {{
                    document.execCommand('copy');
                    confermaCopia();
                }});
            }} else {{
                document.execCommand('copy');
                confermaCopia();
            }}
        }});
    }}
}})();
</script>
"""

        if descrizione_ia:
            content += f"""
<div class="doc-abstract">
    <p>{descrizione_ia}</p>
</div>
"""

        # 🔥 METADATI: "Serie" → "Argomenti", "Parole chiave" rimosso
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
            <span class="metadata-value">{tipo_display if tipo_display else 'N/A'}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Argomenti</span>
            <span class="metadata-value">{serie if serie else 'N/A'}</span>
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
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 1.2rem;
    padding: 0.5rem 1rem 0.8rem 1rem;
    font-size: 0.9rem;
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

.citazione-link {{
    background: none;
    border: none;
    padding: 0;
    color: var(--md-primary-fg-color);
    text-decoration: none;
    font-weight: 500;
    font-size: 0.9rem;
    cursor: pointer;
    font-family: inherit;
}}

.citazione-link:hover {{
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

.text-content {{
    margin: 1rem 0;
    background: var(--md-code-bg-color);
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--md-default-fg-color--lightest);
}}

.text-preview {{
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: inherit;
    font-size: 0.95rem;
    line-height: 1.6;
    padding: 1.5rem;
    margin: 0;
    max-height: 600px;
    overflow-y: auto;
    background: transparent;
    color: var(--md-default-fg-color);
}}

.text-fallback {{
    padding: 2rem;
    text-align: center;
    color: var(--md-default-fg-color--light);
}}

.text-fallback a {{
    color: var(--md-primary-fg-color);
    text-decoration: none;
    font-weight: 500;
}}

.text-fallback a:hover {{
    text-decoration: underline;
}}

.text-bilingue {{
    margin: 1rem 0;
    background: var(--md-code-bg-color);
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--md-default-fg-color--lightest);
}}

.lingua-toggle {{
    display: flex;
    gap: 0.5rem;
    padding: 0.6rem 1rem;
    background: var(--md-default-fg-color--lightest);
    border-bottom: 1px solid var(--md-default-fg-color--light);
}}

.lingua-btn {{
    background: transparent;
    border: 2px solid transparent;
    border-radius: 4px;
    padding: 0.3rem 1rem;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--md-default-fg-color--light);
    cursor: pointer;
    transition: color 0.2s, border-color 0.2s, background 0.2s;
}}

.lingua-btn:hover {{
    color: var(--md-default-fg-color);
}}

.lingua-btn--active {{
    color: var(--md-primary-fg-color);
    border-color: var(--md-primary-fg-color);
    background: rgba(183, 28, 28, 0.08);
}}

.lingua-content {{
    padding: 0;
}}

.lingua-content .text-preview {{
    max-height: 600px;
    overflow-y: auto;
    padding: 1.5rem;
    margin: 0;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: inherit;
    font-size: 0.95rem;
    line-height: 1.6;
    background: transparent;
    color: var(--md-default-fg-color);
}}

.citazione-pannello {{
    background: var(--md-code-bg-color);
    border-top: 1px solid var(--md-default-fg-color--lightest);
    padding: 0.9rem 1rem;
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 0.7rem;
}}

.citazione-testo {{
    width: 100%;
    box-sizing: border-box;
    font-family: 'Roboto Mono', 'Courier New', monospace;
    font-size: 0.85rem;
    line-height: 1.5;
    padding: 0.7rem 0.9rem;
    border-radius: 6px;
    border: 1px solid var(--md-default-fg-color--lightest);
    background: var(--md-default-bg-color);
    color: var(--md-default-fg-color);
    resize: vertical;
}}

.citazione-tabs {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
}}

.citazione-tab {{
    background: transparent;
    border: 1px solid var(--md-default-fg-color--lightest);
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--md-default-fg-color--light);
    cursor: pointer;
    transition: color 0.15s, border-color 0.15s, background 0.15s;
}}

.citazione-tab:hover {{
    color: var(--md-default-fg-color);
}}

.citazione-tab--active {{
    color: #ffffff;
    background: var(--md-primary-fg-color);
    border-color: var(--md-primary-fg-color);
}}

.citazione-copia {{
    align-self: flex-end;
    background: var(--md-primary-fg-color);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 0.4rem 1.2rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
    white-space: nowrap;
}}

.citazione-copia:hover {{
    background: var(--md-primary-fg-color--dark);
}}

@media (max-width: 600px) {{
    .citazione-testo {{
        font-size: 0.78rem;
    }}
    .citazione-copia {{
        align-self: stretch;
    }}
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
    .text-preview {{
        font-size: 0.85rem;
        padding: 1rem;
        max-height: 400px;
    }}
    .lingua-content .text-preview {{
        font-size: 0.85rem;
        padding: 1rem;
        max-height: 400px;
    }}
    .lingua-toggle {{
        padding: 0.4rem 0.8rem;
        gap: 0.3rem;
    }}
    .lingua-btn {{
        padding: 0.2rem 0.6rem;
        font-size: 0.75rem;
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